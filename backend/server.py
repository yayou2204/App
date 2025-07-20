from fastapi import FastAPI, APIRouter, HTTPException, Depends, Form, File, UploadFile, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import JSONResponse
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import uuid
import base64
import hashlib

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app without a prefix
app = FastAPI()

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Security
SECRET_KEY = "infotech_ma_secret_key_2025"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
ADMIN_PASSWORD = "NEW"

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()

# Models
class User(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    email: str
    username: str
    password_hash: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    is_admin: bool = False

class UserCreate(BaseModel):
    email: str
    username: str
    password: str

class UserLogin(BaseModel):
    email: str
    password: str

class AdminLogin(BaseModel):
    password: str

class Product(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    category: str  # CPU, GPU, RAM, MOTHERBOARD, STORAGE, PSU, CASE, COOLING
    brand: str
    price: float
    description: str
    image_base64: str
    stock_quantity: int
    stock_status: str  # "in_stock", "out_of_stock", "coming_soon"
    specifications: Dict[str, Any]
    compatibility_requirements: Dict[str, Any] = {}
    created_at: datetime = Field(default_factory=datetime.utcnow)

class ProductCreate(BaseModel):
    name: str
    category: str
    brand: str
    price: float
    description: str
    image_base64: str = ""
    stock_quantity: int
    specifications: Dict[str, Any] = {}
    compatibility_requirements: Dict[str, Any] = {}

class CartItem(BaseModel):
    product_id: str
    quantity: int
    price: float

class Cart(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    items: List[CartItem] = []
    total: float = 0.0
    promo_code: Optional[str] = None
    discount: float = 0.0
    created_at: datetime = Field(default_factory=datetime.utcnow)

class PromoCode(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    code: str
    discount_percentage: float
    active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)

class ProductFilter(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str  # Nom du filtre (ex: "Prix", "Couleur", "Taille")
    type: str  # Type de filtre: "range" (pour prix), "select" (pour choix multiples), "boolean"
    values: List[str] = []  # Valeurs possibles pour le filtre (ex: ["Rouge", "Bleu", "Vert"])
    field: str  # Champ produit sur lequel filtrer (ex: "price", "specifications.color", "brand")
    active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)

class PCConfiguration(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    name: str
    components: Dict[str, str] = {}  # category -> product_id
    total_price: float
    compatibility_status: bool = True
    compatibility_issues: List[str] = []
    created_at: datetime = Field(default_factory=datetime.utcnow)

# Authentication functions
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        user = await db.users.find_one({"id": user_id})
        if user is None:
            raise HTTPException(status_code=401, detail="User not found")
        return User(**user)
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

async def get_admin_user(user: User = Depends(get_current_user)):
    if not user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    return user

# Compatibility checking functions
def check_cpu_motherboard_compatibility(cpu_spec, motherboard_spec):
    if cpu_spec.get("socket") != motherboard_spec.get("socket"):
        return False, "CPU socket incompatible with motherboard"
    return True, ""

def check_ram_compatibility(ram_spec, motherboard_spec):
    if ram_spec.get("type") not in motherboard_spec.get("supported_memory", []):
        return False, "RAM type not supported by motherboard"
    return True, ""

def check_gpu_compatibility(gpu_spec, motherboard_spec, psu_spec):
    if gpu_spec.get("power_requirement", 0) > psu_spec.get("wattage", 0):
        return False, "PSU insufficient for GPU power requirements"
    return True, ""

async def validate_pc_configuration(components):
    issues = []
    
    # Get component specifications
    component_specs = {}
    for category, product_id in components.items():
        product = await db.products.find_one({"id": product_id})
        if product:
            component_specs[category] = product.get("specifications", {})
    
    # Check CPU-Motherboard compatibility
    if "CPU" in component_specs and "MOTHERBOARD" in component_specs:
        compatible, issue = check_cpu_motherboard_compatibility(
            component_specs["CPU"], component_specs["MOTHERBOARD"]
        )
        if not compatible:
            issues.append(issue)
    
    # Check RAM compatibility
    if "RAM" in component_specs and "MOTHERBOARD" in component_specs:
        compatible, issue = check_ram_compatibility(
            component_specs["RAM"], component_specs["MOTHERBOARD"]
        )
        if not compatible:
            issues.append(issue)
    
    # Check GPU-PSU compatibility
    if "GPU" in component_specs and "PSU" in component_specs:
        compatible, issue = check_gpu_compatibility(
            component_specs["GPU"], component_specs["MOTHERBOARD"], component_specs["PSU"]
        )
        if not compatible:
            issues.append(issue)
    
    return len(issues) == 0, issues

# Routes
@api_router.post("/register")
async def register(user_data: UserCreate):
    # Check if user exists
    existing_user = await db.users.find_one({"email": user_data.email})
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Create user
    user = User(
        email=user_data.email,
        username=user_data.username,
        password_hash=get_password_hash(user_data.password)
    )
    
    await db.users.insert_one(user.dict())
    
    # Create access token
    access_token = create_access_token(data={"sub": user.id})
    return {"access_token": access_token, "token_type": "bearer", "user": {"id": user.id, "username": user.username, "email": user.email}}

@api_router.post("/login")
async def login(user_data: UserLogin):
    user = await db.users.find_one({"email": user_data.email})
    if not user or not verify_password(user_data.password, user["password_hash"]):
        raise HTTPException(status_code=400, detail="Invalid credentials")
    
    access_token = create_access_token(data={"sub": user["id"]})
    return {"access_token": access_token, "token_type": "bearer", "user": {"id": user["id"], "username": user["username"], "email": user["email"]}}

@api_router.post("/admin/login")
async def admin_login(admin_data: AdminLogin):
    if admin_data.password != ADMIN_PASSWORD:
        raise HTTPException(status_code=400, detail="Invalid admin password")
    
    # Create or get admin user
    admin_user = await db.users.find_one({"email": "admin@infotech.ma"})
    if not admin_user:
        admin = User(
            email="admin@infotech.ma",
            username="admin",
            password_hash=get_password_hash(ADMIN_PASSWORD),
            is_admin=True
        )
        await db.users.insert_one(admin.dict())
        admin_user = admin.dict()
    
    access_token = create_access_token(data={"sub": admin_user["id"]})
    return {"access_token": access_token, "token_type": "bearer", "user": {"id": admin_user["id"], "username": "admin", "email": admin_user["email"], "is_admin": True}}

@api_router.get("/products")
async def get_products(request: Request, category: Optional[str] = None, search: Optional[str] = None):
    filter_criteria = {}
    
    # Filtres existants
    if category:
        filter_criteria["category"] = category
    
    if search:
        filter_criteria["$or"] = [
            {"name": {"$regex": search, "$options": "i"}},
            {"brand": {"$regex": search, "$options": "i"}},
            {"description": {"$regex": search, "$options": "i"}}
        ]
    
    # Filtres dynamiques - analyser tous les paramètres de requête
    query_params = dict(request.query_params)
    
    # Récupérer les filtres actifs
    active_filters = await db.product_filters.find({"active": True}).to_list(1000)
    
    for filter_config in active_filters:
        param_name = f"filter_{filter_config['name'].lower().replace(' ', '_')}"
        if param_name in query_params:
            filter_value = query_params[param_name]
            field = filter_config['field']
            filter_type = filter_config['type']
            
            if filter_type == "select" and filter_value:
                # Pour les filtres de sélection (ex: marque, couleur)
                if field.startswith("specifications."):
                    filter_criteria[field] = filter_value
                else:
                    filter_criteria[field] = filter_value
            
            elif filter_type == "range" and filter_value:
                # Pour les filtres de plage (ex: prix)
                try:
                    if ":" in filter_value:  # Format: "min:max"
                        min_val, max_val = filter_value.split(":")
                        range_criteria = {}
                        if min_val:
                            range_criteria["$gte"] = float(min_val)
                        if max_val:
                            range_criteria["$lte"] = float(max_val)
                        if range_criteria:
                            filter_criteria[field] = range_criteria
                    else:
                        # Valeur unique
                        filter_criteria[field] = float(filter_value)
                except ValueError:
                    pass  # Ignorer les valeurs invalides
            
            elif filter_type == "boolean" and filter_value.lower() in ['true', 'false']:
                filter_criteria[field] = filter_value.lower() == 'true'
    
    products = await db.products.find(filter_criteria).to_list(1000)
    return [Product(**product) for product in products]

@api_router.get("/products/{product_id}")
async def get_product(product_id: str):
    product = await db.products.find_one({"id": product_id})
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return Product(**product)

@api_router.post("/admin/products")
async def create_product(product_data: ProductCreate, admin: User = Depends(get_admin_user)):
    # Set stock status based on quantity
    stock_status = "in_stock" if product_data.stock_quantity > 0 else "out_of_stock"
    
    product = Product(
        name=product_data.name,
        category=product_data.category,
        brand=product_data.brand,
        price=product_data.price,
        description=product_data.description,
        image_base64=product_data.image_base64,
        stock_quantity=product_data.stock_quantity,
        stock_status=stock_status,
        specifications=product_data.specifications,
        compatibility_requirements=product_data.compatibility_requirements
    )
    
    await db.products.insert_one(product.dict())
    return product

@api_router.put("/admin/products/{product_id}")
async def update_product(product_id: str, product_data: ProductCreate, admin: User = Depends(get_admin_user)):
    stock_status = "in_stock" if product_data.stock_quantity > 0 else "out_of_stock"
    
    update_data = product_data.dict()
    update_data["stock_status"] = stock_status
    
    result = await db.products.update_one(
        {"id": product_id},
        {"$set": update_data}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Product not found")
    
    return {"message": "Product updated successfully"}

@api_router.delete("/admin/products/{product_id}")
async def delete_product(product_id: str, admin: User = Depends(get_admin_user)):
    result = await db.products.delete_one({"id": product_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Product not found")
    return {"message": "Product deleted successfully"}

@api_router.get("/cart")
async def get_cart(user: User = Depends(get_current_user)):
    cart = await db.carts.find_one({"user_id": user.id})
    if not cart:
        cart = Cart(user_id=user.id)
        await db.carts.insert_one(cart.dict())
        return cart
    return Cart(**cart)

@api_router.post("/cart/add")
async def add_to_cart(product_id: str, quantity: int = 1, user: User = Depends(get_current_user)):
    product = await db.products.find_one({"id": product_id})
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    if product["stock_quantity"] < quantity:
        raise HTTPException(status_code=400, detail="Insufficient stock")
    
    cart = await db.carts.find_one({"user_id": user.id})
    if not cart:
        cart = Cart(user_id=user.id)
    else:
        cart = Cart(**cart)
    
    # Check if item already in cart
    item_found = False
    for item in cart.items:
        if item.product_id == product_id:
            item.quantity += quantity
            item_found = True
            break
    
    if not item_found:
        cart.items.append(CartItem(
            product_id=product_id,
            quantity=quantity,
            price=product["price"]
        ))
    
    # Calculate total
    cart.total = sum(item.quantity * item.price for item in cart.items)
    
    await db.carts.update_one(
        {"user_id": user.id},
        {"$set": cart.dict()},
        upsert=True
    )
    
    return {"message": "Item added to cart"}

@api_router.post("/cart/apply-promo")
async def apply_promo_code(code: str, user: User = Depends(get_current_user)):
    promo = await db.promo_codes.find_one({"code": code, "active": True})
    if not promo:
        raise HTTPException(status_code=404, detail="Invalid promo code")
    
    cart = await db.carts.find_one({"user_id": user.id})
    if not cart:
        raise HTTPException(status_code=404, detail="Cart not found")
    
    cart_obj = Cart(**cart)
    cart_obj.promo_code = code
    cart_obj.discount = cart_obj.total * (promo["discount_percentage"] / 100)
    
    await db.carts.update_one(
        {"user_id": user.id},
        {"$set": cart_obj.dict()}
    )
    
    return {"message": "Promo code applied", "discount": cart_obj.discount}

@api_router.delete("/cart/remove/{product_id}")
async def remove_from_cart(product_id: str, user: User = Depends(get_current_user)):
    cart = await db.carts.find_one({"user_id": user.id})
    if not cart:
        raise HTTPException(status_code=404, detail="Cart not found")
    
    cart_obj = Cart(**cart)
    
    # Find and remove the item
    cart_obj.items = [item for item in cart_obj.items if item.product_id != product_id]
    
    # Recalculate total
    cart_obj.total = sum(item.quantity * item.price for item in cart_obj.items)
    
    # Recalculate discount if promo code is applied
    if cart_obj.promo_code:
        promo = await db.promo_codes.find_one({"code": cart_obj.promo_code, "active": True})
        if promo:
            cart_obj.discount = cart_obj.total * (promo["discount_percentage"] / 100)
        else:
            cart_obj.discount = 0
            cart_obj.promo_code = None
    
    await db.carts.update_one(
        {"user_id": user.id},
        {"$set": cart_obj.dict()}
    )
    
    return {"message": "Item removed from cart"}

@api_router.put("/cart/update/{product_id}")
async def update_cart_quantity(product_id: str, quantity: int, user: User = Depends(get_current_user)):
    if quantity <= 0:
        raise HTTPException(status_code=400, detail="Quantity must be greater than 0")
    
    # Check product availability
    product = await db.products.find_one({"id": product_id})
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    if product["stock_quantity"] < quantity:
        raise HTTPException(status_code=400, detail="Insufficient stock")
    
    cart = await db.carts.find_one({"user_id": user.id})
    if not cart:
        raise HTTPException(status_code=404, detail="Cart not found")
    
    cart_obj = Cart(**cart)
    
    # Find and update the item
    item_found = False
    for item in cart_obj.items:
        if item.product_id == product_id:
            item.quantity = quantity
            item_found = True
            break
    
    if not item_found:
        raise HTTPException(status_code=404, detail="Item not found in cart")
    
    # Recalculate total
    cart_obj.total = sum(item.quantity * item.price for item in cart_obj.items)
    
    # Recalculate discount if promo code is applied
    if cart_obj.promo_code:
        promo = await db.promo_codes.find_one({"code": cart_obj.promo_code, "active": True})
        if promo:
            cart_obj.discount = cart_obj.total * (promo["discount_percentage"] / 100)
        else:
            cart_obj.discount = 0
            cart_obj.promo_code = None
    
    await db.carts.update_one(
        {"user_id": user.id},
        {"$set": cart_obj.dict()}
    )
    
    return {"message": "Cart quantity updated"}

@api_router.post("/admin/promo-codes")
async def create_promo_code(code: str, discount_percentage: float, admin: User = Depends(get_admin_user)):
    promo = PromoCode(code=code, discount_percentage=discount_percentage)
    await db.promo_codes.insert_one(promo.dict())
    return promo

@api_router.get("/admin/promo-codes")
async def get_promo_codes(admin: User = Depends(get_admin_user)):
    promos = await db.promo_codes.find({}).to_list(1000)
    return [PromoCode(**promo) for promo in promos]

@api_router.put("/admin/promo-codes/{promo_id}")
async def update_promo_code(promo_id: str, code: str, discount_percentage: float, admin: User = Depends(get_admin_user)):
    result = await db.promo_codes.update_one(
        {"id": promo_id},
        {"$set": {"code": code, "discount_percentage": discount_percentage}}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Promo code not found")
    
    return {"message": "Promo code updated successfully"}

@api_router.delete("/admin/promo-codes/{promo_id}")
async def delete_promo_code(promo_id: str, admin: User = Depends(get_admin_user)):
    result = await db.promo_codes.delete_one({"id": promo_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Promo code not found")
    return {"message": "Promo code deleted successfully"}

@api_router.put("/admin/promo-codes/{promo_id}/toggle")
async def toggle_promo_code(promo_id: str, active: bool, admin: User = Depends(get_admin_user)):
    result = await db.promo_codes.update_one(
        {"id": promo_id},
        {"$set": {"active": active}}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Promo code not found")
    
    return {"message": f"Promo code {'activated' if active else 'deactivated'} successfully"}

# Product Filters Management Endpoints
@api_router.get("/admin/product-filters")
async def get_product_filters(admin: User = Depends(get_admin_user)):
    filters = await db.product_filters.find({}).to_list(1000)
    return [ProductFilter(**filter_data) for filter_data in filters]

@api_router.post("/admin/product-filters")
async def create_product_filter(
    name: str, 
    type: str, 
    field: str,
    values: List[str] = [],
    admin: User = Depends(get_admin_user)
):
    filter_data = ProductFilter(
        name=name,
        type=type,
        field=field,
        values=values
    )
    await db.product_filters.insert_one(filter_data.dict())
    return filter_data

@api_router.put("/admin/product-filters/{filter_id}")
async def update_product_filter(
    filter_id: str,
    name: str,
    type: str, 
    field: str,
    values: List[str] = [],
    admin: User = Depends(get_admin_user)
):
    result = await db.product_filters.update_one(
        {"id": filter_id},
        {"$set": {
            "name": name,
            "type": type,
            "field": field,
            "values": values
        }}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Product filter not found")
    
    return {"message": "Product filter updated successfully"}

@api_router.delete("/admin/product-filters/{filter_id}")
async def delete_product_filter(filter_id: str, admin: User = Depends(get_admin_user)):
    result = await db.product_filters.delete_one({"id": filter_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Product filter not found")
    return {"message": "Product filter deleted successfully"}

@api_router.put("/admin/product-filters/{filter_id}/toggle")
async def toggle_product_filter(filter_id: str, active: bool, admin: User = Depends(get_admin_user)):
    result = await db.product_filters.update_one(
        {"id": filter_id},
        {"$set": {"active": active}}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Product filter not found")
    
    return {"message": f"Product filter {'activated' if active else 'deactivated'} successfully"}

# Endpoint pour récupérer les filtres actifs pour la page produit
@api_router.get("/product-filters")
async def get_active_product_filters():
    filters = await db.product_filters.find({"active": True}).to_list(1000)
    return [ProductFilter(**filter_data) for filter_data in filters]

@api_router.get("/configurator/categories")
async def get_configurator_categories():
    return {
        "categories": ["CPU", "MOTHERBOARD", "RAM", "GPU", "STORAGE", "PSU", "CASE", "COOLING"]
    }

@api_router.post("/configurator/validate")
async def validate_configuration(components: Dict[str, str], user: User = Depends(get_current_user)):
    compatible, issues = await validate_pc_configuration(components)
    
    # Calculate total price
    total_price = 0
    for product_id in components.values():
        product = await db.products.find_one({"id": product_id})
        if product:
            total_price += product["price"]
    
    return {
        "compatible": compatible,
        "issues": issues,
        "total_price": total_price
    }

@api_router.post("/configurator/save")
async def save_configuration(name: str, components: Dict[str, str], user: User = Depends(get_current_user)):
    compatible, issues = await validate_pc_configuration(components)
    
    total_price = 0
    for product_id in components.values():
        product = await db.products.find_one({"id": product_id})
        if product:
            total_price += product["price"]
    
    config = PCConfiguration(
        user_id=user.id,
        name=name,
        components=components,
        total_price=total_price,
        compatibility_status=compatible,
        compatibility_issues=issues
    )
    
    await db.pc_configurations.insert_one(config.dict())
    return config

@api_router.get("/configurator/my-configs")
async def get_my_configurations(user: User = Depends(get_current_user)):
    configs = await db.pc_configurations.find({"user_id": user.id}).to_list(1000)
    return [PCConfiguration(**config) for config in configs]

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()

# Initialize some sample data
@app.on_event("startup")
async def startup_event():
    # Create sample products if none exist
    product_count = await db.products.count_documents({})
    if product_count == 0:
        sample_products = [
            {
                "id": str(uuid.uuid4()),
                "name": "AMD Ryzen 9 5900X",
                "category": "CPU",
                "brand": "AMD",
                "price": 449.99,
                "description": "12-core, 24-thread processor with exceptional gaming and content creation performance",
                "image_base64": "",
                "stock_quantity": 15,
                "stock_status": "in_stock",
                "specifications": {
                    "cores": 12,
                    "threads": 24,
                    "base_clock": "3.7 GHz",
                    "boost_clock": "4.8 GHz",
                    "socket": "AM4"
                },
                "compatibility_requirements": {"socket": "AM4"},
                "created_at": datetime.utcnow()
            },
            {
                "id": str(uuid.uuid4()),
                "name": "ASUS ROG STRIX B550-F",
                "category": "MOTHERBOARD",
                "brand": "ASUS",
                "price": 189.99,
                "description": "ATX motherboard with PCIe 4.0 support and robust VRM design",
                "image_base64": "",
                "stock_quantity": 8,
                "stock_status": "in_stock",
                "specifications": {
                    "form_factor": "ATX",
                    "socket": "AM4",
                    "supported_memory": ["DDR4"],
                    "memory_slots": 4,
                    "max_memory": "128GB"
                },
                "compatibility_requirements": {},
                "created_at": datetime.utcnow()
            }
        ]
        
        await db.products.insert_many(sample_products)
        
        # Create sample promo codes
        sample_promos = [
            {
                "id": str(uuid.uuid4()),
                "code": "GAMING10",
                "discount_percentage": 10.0,
                "active": True,
                "created_at": datetime.utcnow()
            }
        ]
        
        await db.promo_codes.insert_many(sample_promos)