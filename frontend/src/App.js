import React, { useState, useEffect, useContext, createContext } from "react";
import "./App.css";
import axios from "axios";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Auth Context
const AuthContext = createContext();
const CartContext = createContext();

const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(localStorage.getItem('token'));

  useEffect(() => {
    if (token) {
      axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
      // Get user info from token if needed
      const userData = localStorage.getItem('user');
      if (userData) {
        setUser(JSON.parse(userData));
      }
    }
  }, [token]);

  const login = (tokenData, userData) => {
    localStorage.setItem('token', tokenData);
    localStorage.setItem('user', JSON.stringify(userData));
    setToken(tokenData);
    setUser(userData);
    axios.defaults.headers.common['Authorization'] = `Bearer ${tokenData}`;
  };

  const logout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    setToken(null);
    setUser(null);
    delete axios.defaults.headers.common['Authorization'];
  };

  return (
    <AuthContext.Provider value={{ user, token, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
};

const CartProvider = ({ children }) => {
  const [cartCount, setCartCount] = useState(0);
  const [showCartAnimation, setShowCartAnimation] = useState(false);

  const updateCartCount = async () => {
    try {
      const response = await axios.get(`${API}/cart`);
      const totalItems = response.data.items.reduce((sum, item) => sum + item.quantity, 0);
      setCartCount(totalItems);
    } catch (error) {
      console.error('Erreur lors du chargement du panier:', error);
      setCartCount(0);
    }
  };

  const triggerCartAnimation = () => {
    setShowCartAnimation(true);
    setTimeout(() => setShowCartAnimation(false), 600);
  };

  useEffect(() => {
    updateCartCount();
  }, []);

  return (
    <CartContext.Provider value={{ 
      cartCount, 
      updateCartCount, 
      triggerCartAnimation, 
      showCartAnimation 
    }}>
      {children}
    </CartContext.Provider>
  );
};

const useAuth = () => useContext(AuthContext);
const useCart = () => useContext(CartContext);

// Header Component
const Header = () => {
  const { user, logout } = useAuth();
  const { cartCount, showCartAnimation } = useCart();
  const [searchQuery, setSearchQuery] = useState('');

  const handleSearch = (e) => {
    e.preventDefault();
    if (searchQuery.trim()) {
      // Rediriger vers la page produits avec le paramètre de recherche
      window.location.href = `/products?search=${encodeURIComponent(searchQuery.trim())}`;
    }
  };

  return (
    <header className="bg-blue-900 text-white">
      <div className="container mx-auto px-4">
        <div className="flex items-center justify-between py-4">
          <a href="/" className="text-2xl font-bold">INFOTECH.MA</a>
          
          <div className="flex-1 max-w-2xl mx-8">
            <form onSubmit={handleSearch} className="relative">
              <input
                type="text"
                placeholder="Rechercher des composants PC..."
                className="w-full px-4 py-2 rounded-lg text-gray-800 focus:outline-none focus:ring-2 focus:ring-blue-400"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
              />
              <button
                type="submit"
                className="absolute right-2 top-1/2 transform -translate-y-1/2 text-gray-600 hover:text-blue-600"
              >
                🔍
              </button>
            </form>
          </div>

          <nav className="flex items-center space-x-4">
            <a href="/products" className="hover:text-blue-300">Produits</a>
            <a href="/configurator" className="hover:text-blue-300">Configurateur</a>
            {user ? (
              <div className="flex items-center space-x-4">
                <a href="/cart" className="hover:text-blue-300 relative group">
                  <div className="flex items-center space-x-1">
                    <span>🛒</span>
                    <span>Panier</span>
                    {cartCount > 0 && (
                      <span className={`inline-flex items-center justify-center px-2 py-1 text-xs font-bold leading-none text-white bg-red-600 rounded-full min-w-[20px] h-5 transition-transform duration-300 ${
                        showCartAnimation ? 'animate-bounce scale-125' : ''
                      }`}>
                        {cartCount}
                      </span>
                    )}
                  </div>
                </a>
                <span className="text-blue-300">Bonjour, {user.username}</span>
                {user.is_admin && <a href="/admin" className="bg-red-600 px-3 py-1 rounded hover:bg-red-700">Admin</a>}
                <button onClick={logout} className="bg-red-600 px-3 py-1 rounded hover:bg-red-700">Déconnexion</button>
              </div>
            ) : (
              <div className="space-x-2">
                <a href="/login" className="bg-blue-600 px-4 py-2 rounded hover:bg-blue-700">Connexion</a>
                <a href="/register" className="bg-green-600 px-4 py-2 rounded hover:bg-green-700">Inscription</a>
              </div>
            )}
          </nav>
        </div>
      </div>
    </header>
  );
};

// Homepage Component
const Homepage = () => {
  const [currentSlide, setCurrentSlide] = useState(0);
  
  const heroImages = [
    {
      url: "https://images.unsplash.com/photo-1660855552442-1bae49431379",
      title: "PC Gaming Haute Performance",
      description: "Découvrez nos composants gaming de dernière génération"
    },
    {
      url: "https://images.unsplash.com/photo-1616668010115-8f8ce69a4d04",
      title: "Configurations Complètes",
      description: "Des setups gaming complets pour tous les budgets"
    },
    {
      url: "https://images.unsplash.com/photo-1603732551681-2e91159b9dc2",
      title: "Composants de Qualité",
      description: "Les meilleures marques pour votre configuration"
    }
  ];

  useEffect(() => {
    const interval = setInterval(() => {
      setCurrentSlide((prev) => (prev + 1) % heroImages.length);
    }, 5000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div>
      {/* Hero Carousel */}
      <div className="relative h-96 overflow-hidden">
        {heroImages.map((image, index) => (
          <div
            key={index}
            className={`absolute inset-0 transition-transform duration-500 ease-in-out ${
              index === currentSlide ? 'translate-x-0' : 'translate-x-full'
            }`}
            style={{
              backgroundImage: `linear-gradient(rgba(0,0,0,0.4), rgba(0,0,0,0.4)), url(${image.url})`,
              backgroundSize: 'cover',
              backgroundPosition: 'center'
            }}
          >
            <div className="flex items-center justify-center h-full text-white text-center">
              <div>
                <h1 className="text-4xl font-bold mb-4">{image.title}</h1>
                <p className="text-xl mb-8">{image.description}</p>
                <a 
                  href="/configurator"
                  className="bg-blue-600 text-white px-8 py-3 rounded-lg text-lg font-semibold hover:bg-blue-700 transition-colors"
                >
                  Configurez Votre PC
                </a>
              </div>
            </div>
          </div>
        ))}
        
        {/* Carousel indicators */}
        <div className="absolute bottom-4 left-1/2 transform -translate-x-1/2 flex space-x-2">
          {heroImages.map((_, index) => (
            <button
              key={index}
              className={`w-3 h-3 rounded-full ${
                index === currentSlide ? 'bg-white' : 'bg-white/50'
              }`}
              onClick={() => setCurrentSlide(index)}
            />
          ))}
        </div>
      </div>

      {/* Features Section */}
      <div className="py-16 bg-gray-50">
        <div className="container mx-auto px-4">
          <h2 className="text-3xl font-bold text-center mb-12">Pourquoi Choisir INFOTECH.MA</h2>
          <div className="grid md:grid-cols-3 gap-8">
            <div className="text-center">
              <div className="w-16 h-16 bg-blue-600 rounded-full flex items-center justify-center mx-auto mb-4">
                <span className="text-white text-2xl">🎮</span>
              </div>
              <h3 className="text-xl font-semibold mb-2">Gaming Performance</h3>
              <p className="text-gray-600">Composants optimisés pour le gaming haute performance</p>
            </div>
            <div className="text-center">
              <div className="w-16 h-16 bg-blue-600 rounded-full flex items-center justify-center mx-auto mb-4">
                <span className="text-white text-2xl">✅</span>
              </div>
              <h3 className="text-xl font-semibold mb-2">Compatibilité Garantie</h3>
              <p className="text-gray-600">Notre configurateur vérifie la compatibilité de tous les composants</p>
            </div>
            <div className="text-center">
              <div className="w-16 h-16 bg-blue-600 rounded-full flex items-center justify-center mx-auto mb-4">
                <span className="text-white text-2xl">🚚</span>
              </div>
              <h3 className="text-xl font-semibold mb-2">Livraison Rapide</h3>
              <p className="text-gray-600">Expédition rapide partout au Maroc</p>
            </div>
          </div>
        </div>
      </div>

      {/* About Section */}
      <div className="py-16 bg-white">
        <div className="container mx-auto px-4">
          <div className="max-w-4xl mx-auto text-center">
            <h2 className="text-3xl font-bold mb-8">Votre Partenaire Gaming au Maroc</h2>
            <p className="text-lg text-gray-700 mb-6 leading-relaxed">
              INFOTECH.MA est le spécialiste marocain des composants PC gaming. Depuis notre création, nous nous engageons 
              à fournir aux gamers marocains les meilleurs composants du marché avec un service client exceptionnel.
            </p>
            <p className="text-lg text-gray-700 mb-8 leading-relaxed">
              Que vous soyez un gamer occasionnel ou un passionné d'e-sport, notre équipe d'experts vous accompagne 
              dans le choix et l'assemblage de votre configuration parfaite. Nous travaillons avec les plus grandes 
              marques comme AMD, Intel, NVIDIA, ASUS, MSI, et bien d'autres.
            </p>
            <div className="grid md:grid-cols-2 gap-8 text-left">
              <div>
                <h3 className="text-xl font-semibold mb-4 text-blue-600">Notre Mission</h3>
                <p className="text-gray-700">
                  Démocratiser le gaming haute performance au Maroc en proposant des composants de qualité 
                  à des prix compétitifs, avec des conseils personnalisés et un service après-vente irréprochable.
                </p>
              </div>
              <div>
                <h3 className="text-xl font-semibold mb-4 text-blue-600">Notre Engagement</h3>
                <p className="text-gray-700">
                  Garantir la compatibilité de chaque configuration, offrir les meilleurs prix du marché, 
                  et assurer une livraison rapide et sécurisée dans tout le Royaume.
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Stats Section */}
      <div className="py-16 bg-blue-900 text-white">
        <div className="container mx-auto px-4">
          <div className="grid md:grid-cols-4 gap-8 text-center">
            <div>
              <div className="text-4xl font-bold mb-2">500+</div>
              <div className="text-blue-200">Composants en Stock</div>
            </div>
            <div>
              <div className="text-4xl font-bold mb-2">2000+</div>
              <div className="text-blue-200">Clients Satisfaits</div>
            </div>
            <div>
              <div className="text-4xl font-bold mb-2">24/7</div>
              <div className="text-blue-200">Support Client</div>
            </div>
            <div>
              <div className="text-4xl font-bold mb-2">48h</div>
              <div className="text-blue-200">Livraison Express</div>
            </div>
          </div>
        </div>
      </div>

      {/* CTA Section */}
      <div className="py-16 bg-gray-100">
        <div className="container mx-auto px-4 text-center">
          <h2 className="text-3xl font-bold mb-4">Prêt à Construire Votre PC Gaming ?</h2>
          <p className="text-xl text-gray-600 mb-8">
            Utilisez notre configurateur intelligent pour créer la configuration parfaite selon vos besoins et votre budget.
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <a 
              href="/configurator"
              className="bg-blue-600 text-white px-8 py-3 rounded-lg text-lg font-semibold hover:bg-blue-700 transition-colors"
            >
              Configurez Maintenant
            </a>
            <a 
              href="/products"
              className="bg-gray-600 text-white px-8 py-3 rounded-lg text-lg font-semibold hover:bg-gray-700 transition-colors"
            >
              Parcourir les Produits
            </a>
          </div>
        </div>
      </div>
    </div>
  );
};

// Login Component
const Login = () => {
  const [formData, setFormData] = useState({ email: '', password: '' });
  const [error, setError] = useState('');
  const { login } = useAuth();

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      const response = await axios.post(`${API}/login`, formData);
      login(response.data.access_token, response.data.user);
      window.location.href = '/';
    } catch (error) {
      setError(error.response?.data?.detail || 'Erreur de connexion');
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center py-12">
      <div className="max-w-md w-full bg-white p-8 rounded-lg shadow-md">
        <h2 className="text-2xl font-bold text-center mb-6">Connexion</h2>
        {error && <div className="bg-red-100 text-red-700 p-3 rounded mb-4">{error}</div>}
        <form onSubmit={handleSubmit}>
          <div className="mb-4">
            <label className="block text-gray-700 text-sm font-bold mb-2">
              Email
            </label>
            <input
              type="email"
              className="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-400"
              value={formData.email}
              onChange={(e) => setFormData({...formData, email: e.target.value})}
              required
            />
          </div>
          <div className="mb-6">
            <label className="block text-gray-700 text-sm font-bold mb-2">
              Mot de passe
            </label>
            <input
              type="password"
              className="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-400"
              value={formData.password}
              onChange={(e) => setFormData({...formData, password: e.target.value})}
              required
            />
          </div>
          <button
            type="submit"
            className="w-full bg-blue-600 text-white py-2 px-4 rounded-lg hover:bg-blue-700 transition-colors"
          >
            Se connecter
          </button>
        </form>
        <p className="text-center mt-4">
          Pas de compte? <a href="/register" className="text-blue-600 hover:underline">Inscrivez-vous</a>
        </p>
        <p className="text-center mt-2">
          <a href="/admin-login" className="text-red-600 hover:underline">Connexion Admin</a>
        </p>
      </div>
    </div>
  );
};

// Register Component
const Register = () => {
  const [formData, setFormData] = useState({ email: '', username: '', password: '' });
  const [error, setError] = useState('');
  const { login } = useAuth();

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      const response = await axios.post(`${API}/register`, formData);
      login(response.data.access_token, response.data.user);
      window.location.href = '/';
    } catch (error) {
      setError(error.response?.data?.detail || 'Erreur lors de l\'inscription');
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center py-12">
      <div className="max-w-md w-full bg-white p-8 rounded-lg shadow-md">
        <h2 className="text-2xl font-bold text-center mb-6">Inscription</h2>
        {error && <div className="bg-red-100 text-red-700 p-3 rounded mb-4">{error}</div>}
        <form onSubmit={handleSubmit}>
          <div className="mb-4">
            <label className="block text-gray-700 text-sm font-bold mb-2">
              Nom d'utilisateur
            </label>
            <input
              type="text"
              className="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-400"
              value={formData.username}
              onChange={(e) => setFormData({...formData, username: e.target.value})}
              required
            />
          </div>
          <div className="mb-4">
            <label className="block text-gray-700 text-sm font-bold mb-2">
              Email
            </label>
            <input
              type="email"
              className="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-400"
              value={formData.email}
              onChange={(e) => setFormData({...formData, email: e.target.value})}
              required
            />
          </div>
          <div className="mb-6">
            <label className="block text-gray-700 text-sm font-bold mb-2">
              Mot de passe
            </label>
            <input
              type="password"
              className="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-400"
              value={formData.password}
              onChange={(e) => setFormData({...formData, password: e.target.value})}
              required
            />
          </div>
          <button
            type="submit"
            className="w-full bg-green-600 text-white py-2 px-4 rounded-lg hover:bg-green-700 transition-colors"
          >
            S'inscrire
          </button>
        </form>
        <p className="text-center mt-4">
          Déjà un compte? <a href="/login" className="text-blue-600 hover:underline">Connectez-vous</a>
        </p>
      </div>
    </div>
  );
};

// Admin Login Component
const AdminLogin = () => {
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const { login } = useAuth();

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      const response = await axios.post(`${API}/admin/login`, { password });
      login(response.data.access_token, response.data.user);
      window.location.href = '/admin';
    } catch (error) {
      setError('Mot de passe administrateur incorrect');
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center py-12">
      <div className="max-w-md w-full bg-white p-8 rounded-lg shadow-md">
        <h2 className="text-2xl font-bold text-center mb-6">Connexion Administrateur</h2>
        {error && <div className="bg-red-100 text-red-700 p-3 rounded mb-4">{error}</div>}
        <form onSubmit={handleSubmit}>
          <div className="mb-6">
            <label className="block text-gray-700 text-sm font-bold mb-2">
              Mot de passe administrateur
            </label>
            <input
              type="password"
              className="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-400"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
            />
          </div>
          <button
            type="submit"
            className="w-full bg-red-600 text-white py-2 px-4 rounded-lg hover:bg-red-700 transition-colors"
          >
            Se connecter
          </button>
        </form>
        <p className="text-center mt-4">
          <a href="/login" className="text-blue-600 hover:underline">Retour à la connexion normale</a>
        </p>
      </div>
    </div>
  );
};

// Products Component
const Products = () => {
  const { updateCartCount, triggerCartAnimation } = useCart();
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [category, setCategory] = useState('');
  const [searchQuery, setSearchQuery] = useState('');
  const [priceRange, setPriceRange] = useState('');
  const [selectedBrand, setSelectedBrand] = useState('');
  const [selectedSeries, setSelectedSeries] = useState('');

  const categories = ['CPU', 'GPU', 'RAM', 'MOTHERBOARD', 'STORAGE', 'PSU', 'CASE', 'COOLING'];
  const priceRanges = [
    { label: 'Tous les prix', value: '' },
    { label: 'Moins de 200 MAD', value: '0-200' },
    { label: '200 - 500 MAD', value: '200-500' },
    { label: '500 - 1000 MAD', value: '500-1000' },
    { label: '1000 - 2000 MAD', value: '1000-2000' },
    { label: 'Plus de 2000 MAD', value: '2000-999999' }
  ];

  // Brand options based on category
  const getBrandOptions = () => {
    const brands = new Set();
    products.forEach(product => {
      if (!category || product.category === category) {
        brands.add(product.brand);
      }
    });
    return Array.from(brands).sort();
  };

  // Series options for CPU and GPU
  const getSeriesOptions = () => {
    if (!category || (category !== 'CPU' && category !== 'GPU')) return [];
    
    const series = new Set();
    products.forEach(product => {
      if (product.category === category) {
        // Extract series from product name
        if (category === 'CPU') {
          // For CPU: extract series like "Ryzen 9", "Core i7", etc.
          const cpuSeries = product.name.match(/(Ryzen \d+|Core i\d+|FX-\d+|Athlon|Pentium)/i);
          if (cpuSeries) series.add(cpuSeries[1]);
        } else if (category === 'GPU') {
          // For GPU: extract series like "RTX 4080", "GTX 1660", "RX 7800", etc.
          const gpuSeries = product.name.match(/(RTX \d+|GTX \d+|RX \d+|Arc A\d+)/i);
          if (gpuSeries) series.add(gpuSeries[1]);
        }
      }
    });
    return Array.from(series).sort();
  };

  // Read URL parameters on component mount
  useEffect(() => {
    const urlParams = new URLSearchParams(window.location.search);
    const urlSearch = urlParams.get('search');
    const urlCategory = urlParams.get('category');
    
    if (urlSearch) setSearchQuery(urlSearch);
    if (urlCategory) setCategory(urlCategory);
  }, []);

  useEffect(() => {
    fetchProducts();
  }, [category, searchQuery]);

  useEffect(() => {
    // Reset brand and series filters when category changes
    setSelectedBrand('');
    setSelectedSeries('');
  }, [category]);

  const fetchProducts = async () => {
    try {
      const params = new URLSearchParams();
      if (category) params.append('category', category);
      if (searchQuery) params.append('search', searchQuery);
      
      const response = await axios.get(`${API}/products?${params}`);
      setProducts(response.data);
    } catch (error) {
      console.error('Erreur lors du chargement des produits:', error);
    } finally {
      setLoading(false);
    }
  };

  const addToCart = async (productId) => {
    try {
      await axios.post(`${API}/cart/add?product_id=${productId}&quantity=1`);
      
      // Déclencher l'animation et mettre à jour le compteur
      triggerCartAnimation();
      await updateCartCount();
      
      // Animation de succès plus subtile
      const button = event.target;
      const originalText = button.textContent;
      button.textContent = '✅ Ajouté !';
      button.classList.add('bg-green-600');
      button.classList.remove('bg-blue-600');
      
      setTimeout(() => {
        button.textContent = originalText;
        button.classList.remove('bg-green-600');
        button.classList.add('bg-blue-600');
      }, 1500);
      
    } catch (error) {
      alert('Erreur lors de l\'ajout au panier');
    }
  };

  const getStockBadge = (product) => {
    switch (product.stock_status) {
      case 'in_stock':
        return <span className="bg-green-100 text-green-800 text-xs px-2 py-1 rounded-full">En stock ({product.stock_quantity})</span>;
      case 'out_of_stock':
        return <span className="bg-red-100 text-red-800 text-xs px-2 py-1 rounded-full">Rupture de stock</span>;
      case 'coming_soon':
        return <span className="bg-yellow-100 text-yellow-800 text-xs px-2 py-1 rounded-full">Bientôt disponible</span>;
      default:
        return null;
    }
  };

  const filterProducts = (products) => {
    let filtered = [...products];
    
    // Filter by price range
    if (priceRange) {
      const [min, max] = priceRange.split('-').map(Number);
      filtered = filtered.filter(product => {
        const price = product.price;
        return price >= min && price <= max;
      });
    }
    
    // Filter by brand
    if (selectedBrand) {
      filtered = filtered.filter(product => product.brand === selectedBrand);
    }
    
    // Filter by series
    if (selectedSeries) {
      filtered = filtered.filter(product => {
        return product.name.toLowerCase().includes(selectedSeries.toLowerCase());
      });
    }
    
    return filtered;
  };

  const filteredProducts = filterProducts(products);

  if (loading) return <div className="text-center py-8">Chargement...</div>;

  const brandOptions = getBrandOptions();
  const seriesOptions = getSeriesOptions();

  return (
    <div className="container mx-auto px-4 py-8">
      <h1 className="text-3xl font-bold mb-8">Nos Produits</h1>
      
      {/* Category Filters */}
      <div className="mb-6">
        <h3 className="text-lg font-semibold mb-3">Catégories</h3>
        <div className="flex flex-wrap gap-2">
          <button
            onClick={() => setCategory('')}
            className={`px-4 py-2 rounded ${category === '' ? 'bg-blue-600 text-white' : 'bg-gray-200 text-gray-700 hover:bg-gray-300'}`}
          >
            Toutes les catégories
          </button>
          {categories.map(cat => (
            <button
              key={cat}
              onClick={() => setCategory(cat)}
              className={`px-4 py-2 rounded ${category === cat ? 'bg-blue-600 text-white' : 'bg-gray-200 text-gray-700 hover:bg-gray-300'}`}
            >
              {cat}
            </button>
          ))}
        </div>
      </div>

      {/* Brand Filters */}
      {brandOptions.length > 0 && (
        <div className="mb-6">
          <h3 className="text-lg font-semibold mb-3">Marques</h3>
          <div className="flex flex-wrap gap-2">
            <button
              onClick={() => setSelectedBrand('')}
              className={`px-4 py-2 rounded ${selectedBrand === '' ? 'bg-purple-600 text-white' : 'bg-gray-200 text-gray-700 hover:bg-gray-300'}`}
            >
              Toutes les marques
            </button>
            {brandOptions.map(brand => (
              <button
                key={brand}
                onClick={() => setSelectedBrand(brand)}
                className={`px-4 py-2 rounded ${selectedBrand === brand ? 'bg-purple-600 text-white' : 'bg-gray-200 text-gray-700 hover:bg-gray-300'}`}
              >
                {brand}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Series/Model Filters for CPU and GPU */}
      {seriesOptions.length > 0 && (category === 'CPU' || category === 'GPU') && (
        <div className="mb-6">
          <h3 className="text-lg font-semibold mb-3">
            {category === 'CPU' ? 'Séries de Processeurs' : 'Séries de Cartes Graphiques'}
          </h3>
          <div className="flex flex-wrap gap-2">
            <button
              onClick={() => setSelectedSeries('')}
              className={`px-4 py-2 rounded ${selectedSeries === '' ? 'bg-orange-600 text-white' : 'bg-gray-200 text-gray-700 hover:bg-gray-300'}`}
            >
              Toutes les séries
            </button>
            {seriesOptions.map(series => (
              <button
                key={series}
                onClick={() => setSelectedSeries(series)}
                className={`px-4 py-2 rounded ${selectedSeries === series ? 'bg-orange-600 text-white' : 'bg-gray-200 text-gray-700 hover:bg-gray-300'}`}
              >
                {series}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Price Filters */}
      <div className="mb-8">
        <h3 className="text-lg font-semibold mb-3">Filtrer par Prix</h3>
        <div className="flex flex-wrap gap-2">
          {priceRanges.map(range => (
            <button
              key={range.value}
              onClick={() => setPriceRange(range.value)}
              className={`px-4 py-2 rounded ${priceRange === range.value ? 'bg-green-600 text-white' : 'bg-gray-200 text-gray-700 hover:bg-gray-300'}`}
            >
              {range.label}
            </button>
          ))}
        </div>
      </div>

      {/* Active Filters Summary */}
      {(category || selectedBrand || selectedSeries || priceRange) && (
        <div className="mb-6 p-4 bg-blue-50 rounded-lg">
          <h4 className="font-semibold mb-2">Filtres actifs:</h4>
          <div className="flex flex-wrap gap-2">
            {category && (
              <span className="bg-blue-100 text-blue-800 px-3 py-1 rounded-full text-sm">
                Catégorie: {category}
              </span>
            )}
            {selectedBrand && (
              <span className="bg-purple-100 text-purple-800 px-3 py-1 rounded-full text-sm">
                Marque: {selectedBrand}
              </span>
            )}
            {selectedSeries && (
              <span className="bg-orange-100 text-orange-800 px-3 py-1 rounded-full text-sm">
                Série: {selectedSeries}
              </span>
            )}
            {priceRange && (
              <span className="bg-green-100 text-green-800 px-3 py-1 rounded-full text-sm">
                Prix: {priceRanges.find(r => r.value === priceRange)?.label}
              </span>
            )}
            <button
              onClick={() => {
                setCategory('');
                setSelectedBrand('');
                setSelectedSeries('');
                setPriceRange('');
              }}
              className="bg-red-100 text-red-800 px-3 py-1 rounded-full text-sm hover:bg-red-200"
            >
              Effacer tous les filtres
            </button>
          </div>
        </div>
      )}

      {/* Products Grid */}
      <div className="grid md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
        {filteredProducts.map(product => (
          <div key={product.id} className="bg-white rounded-lg shadow-md overflow-hidden">
            <div className="h-48 bg-gray-200 flex items-center justify-center">
              {product.image_base64 ? (
                <img 
                  src={`data:image/jpeg;base64,${product.image_base64}`} 
                  alt={product.name}
                  className="w-full h-full object-cover"
                />
              ) : (
                <div className="text-gray-400 text-center">
                  <div className="text-4xl mb-2">📦</div>
                  <div>Image non disponible</div>
                </div>
              )}
            </div>
            <div className="p-4">
              <h3 className="font-semibold text-lg mb-2">{product.name}</h3>
              <p className="text-gray-600 text-sm mb-2">{product.brand}</p>
              <p className="text-blue-600 font-bold text-xl mb-2">{product.price} MAD</p>
              <div className="mb-3">
                {getStockBadge(product)}
              </div>
              <div className="flex space-x-2">
                <a 
                  href={`/product/${product.id}`}
                  className="flex-1 bg-gray-600 text-white py-2 px-4 rounded text-center hover:bg-gray-700"
                >
                  Voir détails
                </a>
                {product.stock_status === 'in_stock' && (
                  <button
                    onClick={() => addToCart(product.id)}
                    className="flex-1 bg-blue-600 text-white py-2 px-4 rounded hover:bg-blue-700"
                  >
                    Ajouter
                  </button>
                )}
              </div>
            </div>
          </div>
        ))}
      </div>
      
      {filteredProducts.length === 0 && (
        <div className="text-center py-12">
          <p className="text-gray-500 text-lg mb-2">Aucun produit trouvé</p>
          <p className="text-gray-400">
            Essayez de modifier vos critères de filtre ou{' '}
            <button 
              onClick={() => {
                setCategory('');
                setSelectedBrand('');
                setSelectedSeries('');
                setPriceRange('');
              }}
              className="text-blue-600 hover:underline"
            >
              effacer tous les filtres
            </button>
          </p>
        </div>
      )}

      {/* Product Statistics */}
      <div className="mt-12 bg-blue-50 p-6 rounded-lg">
        <h3 className="text-xl font-semibold mb-4 text-blue-800">Statistiques des Produits</h3>
        <div className="grid md:grid-cols-4 gap-4 text-center">
          <div className="bg-white p-4 rounded">
            <div className="text-2xl font-bold text-blue-600">{products.length}</div>
            <div className="text-gray-600">Total produits</div>
          </div>
          <div className="bg-white p-4 rounded">
            <div className="text-2xl font-bold text-green-600">{filteredProducts.length}</div>
            <div className="text-gray-600">Produits filtrés</div>
          </div>
          <div className="bg-white p-4 rounded">
            <div className="text-2xl font-bold text-green-600">
              {products.filter(p => p.stock_status === 'in_stock').length}
            </div>
            <div className="text-gray-600">En stock</div>
          </div>
          <div className="bg-white p-4 rounded">
            <div className="text-2xl font-bold text-orange-600">
              {new Set(products.map(p => p.brand)).size}
            </div>
            <div className="text-gray-600">Marques partenaires</div>
          </div>
        </div>
      </div>
    </div>
  );
};

// Product Detail Component
const ProductDetail = ({ productId }) => {
  const { updateCartCount, triggerCartAnimation } = useCart();
  const [product, setProduct] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchProduct();
  }, [productId]);

  const fetchProduct = async () => {
    try {
      const response = await axios.get(`${API}/products/${productId}`);
      setProduct(response.data);
    } catch (error) {
      console.error('Erreur lors du chargement du produit:', error);
    } finally {
      setLoading(false);
    }
  };

  const addToCart = async () => {
    try {
      await axios.post(`${API}/cart/add?product_id=${productId}&quantity=1`);
      
      // Déclencher l'animation et mettre à jour le compteur
      triggerCartAnimation();
      await updateCartCount();
      
      // Animation de succès
      const button = event.target;
      const originalText = button.textContent;
      button.textContent = '✅ Ajouté au panier !';
      button.classList.add('bg-green-600');
      button.classList.remove('bg-blue-600');
      
      setTimeout(() => {
        button.textContent = originalText;
        button.classList.remove('bg-green-600');
        button.classList.add('bg-blue-600');
      }, 2000);
      
    } catch (error) {
      alert('Erreur lors de l\'ajout au panier');
    }
  };

  if (loading) return <div className="text-center py-8">Chargement...</div>;
  if (!product) return <div className="text-center py-8">Produit non trouvé</div>;

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="grid md:grid-cols-2 gap-8">
        <div className="bg-gray-200 h-96 rounded-lg flex items-center justify-center">
          {product.image_base64 ? (
            <img 
              src={`data:image/jpeg;base64,${product.image_base64}`} 
              alt={product.name}
              className="max-w-full max-h-full object-contain"
            />
          ) : (
            <div className="text-gray-400 text-center">
              <div className="text-6xl mb-4">📦</div>
              <div>Image non disponible</div>
            </div>
          )}
        </div>
        <div>
          <h1 className="text-3xl font-bold mb-2">{product.name}</h1>
          <p className="text-gray-600 mb-4">{product.brand}</p>
          <p className="text-blue-600 font-bold text-3xl mb-4">{product.price} MAD</p>
          
          {/* Stock Status */}
          <div className="mb-6">
            {product.stock_status === 'in_stock' && (
              <span className="bg-green-100 text-green-800 px-3 py-1 rounded-full">
                En stock ({product.stock_quantity} disponibles)
              </span>
            )}
            {product.stock_status === 'out_of_stock' && (
              <span className="bg-red-100 text-red-800 px-3 py-1 rounded-full">Rupture de stock</span>
            )}
            {product.stock_status === 'coming_soon' && (
              <span className="bg-yellow-100 text-yellow-800 px-3 py-1 rounded-full">Bientôt disponible</span>
            )}
          </div>

          <div className="mb-6">
            <h3 className="text-xl font-semibold mb-2">Description</h3>
            <p className="text-gray-700">{product.description}</p>
          </div>

          {/* Specifications */}
          {Object.keys(product.specifications).length > 0 && (
            <div className="mb-6">
              <h3 className="text-xl font-semibold mb-2">Spécifications</h3>
              <div className="bg-gray-50 p-4 rounded">
                {Object.entries(product.specifications).map(([key, value]) => (
                  <div key={key} className="flex justify-between py-1">
                    <span className="capitalize">{key.replace('_', ' ')}:</span>
                    <span className="font-medium">{value}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {product.stock_status === 'in_stock' && (
            <button
              onClick={addToCart}
              className="bg-blue-600 text-white py-3 px-8 rounded-lg text-lg font-semibold hover:bg-blue-700 transition-colors"
            >
              Ajouter au panier
            </button>
          )}
        </div>
      </div>
    </div>
  );
};

// PC Configurator Component
const PCConfigurator = () => {
  const { user } = useAuth();
  const [categories] = useState(['CPU', 'MOTHERBOARD', 'RAM', 'GPU', 'STORAGE', 'PSU', 'CASE', 'COOLING']);
  const [selectedComponents, setSelectedComponents] = useState({});
  const [availableProducts, setAvailableProducts] = useState({});
  const [compatibilityResult, setCompatibilityResult] = useState(null);
  const [configName, setConfigName] = useState('');

  useEffect(() => {
    loadProductsForCategories();
  }, []);

  const loadProductsForCategories = async () => {
    const products = {};
    for (const category of categories) {
      try {
        const response = await axios.get(`${API}/products?category=${category}`);
        products[category] = response.data;
      } catch (error) {
        console.error(`Erreur lors du chargement des produits ${category}:`, error);
      }
    }
    setAvailableProducts(products);
  };

  const selectComponent = (category, productId) => {
    setSelectedComponents({
      ...selectedComponents,
      [category]: productId
    });
  };

  const validateConfiguration = async () => {
    if (Object.keys(selectedComponents).length === 0) {
      alert('Veuillez sélectionner au moins un composant');
      return;
    }

    try {
      const response = await axios.post(`${API}/configurator/validate`, selectedComponents);
      setCompatibilityResult(response.data);
    } catch (error) {
      console.error('Erreur lors de la validation:', error);
    }
  };

  const saveConfiguration = async () => {
    if (!user) {
      alert('Veuillez vous connecter pour sauvegarder votre configuration');
      return;
    }

    if (!configName) {
      alert('Veuillez donner un nom à votre configuration');
      return;
    }

    try {
      await axios.post(`${API}/configurator/save`, {
        name: configName,
        components: selectedComponents
      });
      alert('Configuration sauvegardée avec succès !');
      setConfigName('');
    } catch (error) {
      console.error('Erreur lors de la sauvegarde:', error);
      alert('Erreur lors de la sauvegarde');
    }
  };

  const getSelectedProductInfo = (category) => {
    const productId = selectedComponents[category];
    if (!productId || !availableProducts[category]) return null;
    
    return availableProducts[category].find(p => p.id === productId);
  };

  return (
    <div className="container mx-auto px-4 py-8">
      <h1 className="text-3xl font-bold mb-8">Configurateur PC</h1>

      {/* Component Selection */}
      <div className="grid lg:grid-cols-2 gap-8">
        <div>
          <h2 className="text-2xl font-semibold mb-6">Sélectionnez vos composants</h2>
          
          {categories.map(category => (
            <div key={category} className="mb-6 border rounded-lg p-4">
              <h3 className="text-lg font-semibold mb-3">{category}</h3>
              
              {selectedComponents[category] ? (
                <div className="bg-blue-50 p-3 rounded mb-3">
                  {(() => {
                    const product = getSelectedProductInfo(category);
                    return product ? (
                      <div className="flex justify-between items-center">
                        <div>
                          <div className="font-medium">{product.name}</div>
                          <div className="text-blue-600 font-semibold">{product.price} MAD</div>
                        </div>
                        <button
                          onClick={() => {
                            const newComponents = {...selectedComponents};
                            delete newComponents[category];
                            setSelectedComponents(newComponents);
                          }}
                          className="text-red-600 hover:text-red-800"
                        >
                          ✕
                        </button>
                      </div>
                    ) : null;
                  })()}
                </div>
              ) : (
                <div className="space-y-2 max-h-40 overflow-y-auto">
                  {availableProducts[category]?.map(product => (
                    <button
                      key={product.id}
                      onClick={() => selectComponent(category, product.id)}
                      className="w-full text-left p-2 border rounded hover:bg-gray-50 flex justify-between items-center"
                      disabled={product.stock_status !== 'in_stock'}
                    >
                      <div>
                        <div className="font-medium">{product.name}</div>
                        <div className="text-sm text-gray-600">{product.brand}</div>
                      </div>
                      <div className="text-right">
                        <div className="text-blue-600 font-semibold">{product.price} MAD</div>
                        {product.stock_status !== 'in_stock' && (
                          <div className="text-xs text-red-600">Non disponible</div>
                        )}
                      </div>
                    </button>
                  )) || <div className="text-gray-500">Chargement...</div>}
                </div>
              )}
            </div>
          ))}
        </div>

        {/* Configuration Summary */}
        <div>
          <h2 className="text-2xl font-semibold mb-6">Résumé de la configuration</h2>
          
          <div className="bg-white border rounded-lg p-6 sticky top-4">
            {Object.keys(selectedComponents).length === 0 ? (
              <p className="text-gray-500 text-center">Aucun composant sélectionné</p>
            ) : (
              <>
                <div className="space-y-3 mb-6">
                  {Object.entries(selectedComponents).map(([category, productId]) => {
                    const product = getSelectedProductInfo(category);
                    return product ? (
                      <div key={category} className="flex justify-between">
                        <span>{category}: {product.name}</span>
                        <span className="font-semibold">{product.price} MAD</span>
                      </div>
                    ) : null;
                  })}
                </div>

                <div className="border-t pt-4 mb-6">
                  <div className="flex justify-between text-lg font-bold">
                    <span>Prix total:</span>
                    <span>
                      {Object.entries(selectedComponents).reduce((total, [category, productId]) => {
                        const product = getSelectedProductInfo(category);
                        return total + (product ? product.price : 0);
                      }, 0)} MAD
                    </span>
                  </div>
                </div>

                <button
                  onClick={validateConfiguration}
                  className="w-full bg-blue-600 text-white py-2 rounded mb-3 hover:bg-blue-700"
                >
                  Vérifier la compatibilité
                </button>

                {compatibilityResult && (
                  <div className={`p-3 rounded mb-3 ${
                    compatibilityResult.compatible ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                  }`}>
                    <div className="font-semibold">
                      {compatibilityResult.compatible ? '✅ Configuration compatible' : '❌ Problèmes de compatibilité'}
                    </div>
                    {compatibilityResult.issues.length > 0 && (
                      <ul className="mt-2 text-sm">
                        {compatibilityResult.issues.map((issue, index) => (
                          <li key={index}>• {issue}</li>
                        ))}
                      </ul>
                    )}
                  </div>
                )}

                {user && (
                  <>
                    <input
                      type="text"
                      placeholder="Nom de la configuration"
                      value={configName}
                      onChange={(e) => setConfigName(e.target.value)}
                      className="w-full p-2 border rounded mb-3 focus:outline-none focus:ring-2 focus:ring-blue-400"
                    />
                    <button
                      onClick={saveConfiguration}
                      className="w-full bg-green-600 text-white py-2 rounded hover:bg-green-700"
                    >
                      Sauvegarder la configuration
                    </button>
                  </>
                )}
              </>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

// Cart Component
const Cart = () => {
  const { updateCartCount } = useCart();
  const [cart, setCart] = useState({ items: [], total: 0, discount: 0 });
  const [cartItemsWithDetails, setCartItemsWithDetails] = useState([]);
  const [promoCode, setPromoCode] = useState('');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchCart();
  }, []);

  const fetchCart = async () => {
    try {
      const response = await axios.get(`${API}/cart`);
      const cartData = response.data;
      setCart(cartData);
      
      // Récupérer les détails des produits pour chaque item du panier
      const itemsWithDetails = await Promise.all(
        cartData.items.map(async (item) => {
          try {
            const productResponse = await axios.get(`${API}/products/${item.product_id}`);
            return {
              ...item,
              product: productResponse.data
            };
          } catch (error) {
            console.error(`Erreur lors du chargement du produit ${item.product_id}:`, error);
            return {
              ...item,
              product: { 
                name: 'Produit indisponible',
                image_base64: '',
                brand: 'Inconnu'
              }
            };
          }
        })
      );
      
      setCartItemsWithDetails(itemsWithDetails);
    } catch (error) {
      console.error('Erreur lors du chargement du panier:', error);
    } finally {
      setLoading(false);
    }
  };

  const removeFromCart = async (productId) => {
    try {
      // Ici on peut ajouter un endpoint pour supprimer du panier
      // Pour l'instant, on recharge juste le panier
      await fetchCart();
      await updateCartCount();
    } catch (error) {
      console.error('Erreur lors de la suppression:', error);
    }
  };

  const updateQuantity = async (productId, newQuantity) => {
    if (newQuantity <= 0) {
      removeFromCart(productId);
      return;
    }
    
    try {
      // Ici on peut ajouter un endpoint pour modifier la quantité
      // Pour l'instant, on recharge juste le panier
      await fetchCart();
      await updateCartCount();
    } catch (error) {
      console.error('Erreur lors de la mise à jour:', error);
    }
  };

  const applyPromoCode = async () => {
    if (!promoCode) return;
    
    try {
      await axios.post(`${API}/cart/apply-promo?code=${promoCode}`);
      await fetchCart();
      setPromoCode('');
      alert('Code promo appliqué avec succès !');
    } catch (error) {
      alert('Code promo invalide');
    }
  };

  if (loading) return <div className="text-center py-8">Chargement...</div>;

  return (
    <div className="container mx-auto px-4 py-8">
      <h1 className="text-3xl font-bold mb-8">Mon Panier</h1>

      {cartItemsWithDetails.length === 0 ? (
        <div className="text-center py-12">
          <p className="text-gray-500 mb-4">Votre panier est vide</p>
          <a href="/products" className="bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700">
            Continuer les achats
          </a>
        </div>
      ) : (
        <div className="grid lg:grid-cols-3 gap-8">
          <div className="lg:col-span-2">
            <div className="bg-white rounded-lg shadow">
              {cartItemsWithDetails.map((item, index) => (
                <div key={index} className="p-6 border-b flex items-center space-x-4">
                  {/* Image du produit */}
                  <div className="w-20 h-20 bg-gray-200 rounded-lg flex-shrink-0">
                    {item.product.image_base64 ? (
                      <img 
                        src={`data:image/jpeg;base64,${item.product.image_base64}`} 
                        alt={item.product.name}
                        className="w-full h-full object-cover rounded-lg"
                      />
                    ) : (
                      <div className="w-full h-full bg-gray-300 rounded-lg flex items-center justify-center">
                        <span className="text-gray-500 text-xs">Pas d'image</span>
                      </div>
                    )}
                  </div>
                  
                  {/* Détails du produit */}
                  <div className="flex-1">
                    <h3 className="font-semibold text-lg">{item.product.name}</h3>
                    <p className="text-gray-600">{item.product.brand}</p>
                    <p className="text-blue-600 font-semibold">{item.price} MAD</p>
                  </div>
                  
                  {/* Contrôles de quantité */}
                  <div className="flex items-center space-x-2">
                    <button 
                      onClick={() => updateQuantity(item.product_id, item.quantity - 1)}
                      className="w-8 h-8 bg-gray-200 rounded-full flex items-center justify-center hover:bg-gray-300 transition-colors"
                    >
                      -
                    </button>
                    <span className="w-8 text-center font-semibold">{item.quantity}</span>
                    <button 
                      onClick={() => updateQuantity(item.product_id, item.quantity + 1)}
                      className="w-8 h-8 bg-gray-200 rounded-full flex items-center justify-center hover:bg-gray-300 transition-colors"
                    >
                      +
                    </button>
                  </div>
                  
                  {/* Prix total et suppression */}
                  <div className="text-right">
                    <p className="text-lg font-bold">{(item.quantity * item.price).toFixed(2)} MAD</p>
                    <button 
                      onClick={() => removeFromCart(item.product_id)}
                      className="text-red-600 hover:text-red-800 text-sm mt-1"
                    >
                      Supprimer
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div className="lg:col-span-1">
            <div className="bg-white p-6 rounded-lg shadow sticky top-4">
              <h2 className="text-xl font-semibold mb-4">Résumé</h2>
              
              <div className="space-y-2 mb-4">
                <div className="flex justify-between">
                  <span>Sous-total ({cartItemsWithDetails.reduce((sum, item) => sum + item.quantity, 0)} articles):</span>
                  <span>{cart.total} MAD</span>
                </div>
                {cart.discount > 0 && (
                  <div className="flex justify-between text-green-600">
                    <span>Remise ({cart.promo_code}):</span>
                    <span>-{cart.discount} MAD</span>
                  </div>
                )}
                <div className="border-t pt-2">
                  <div className="flex justify-between text-lg font-bold">
                    <span>Total:</span>
                    <span>{(cart.total - cart.discount).toFixed(2)} MAD</span>
                  </div>
                </div>
              </div>

              <div className="mb-4">
                <div className="flex">
                  <input
                    type="text"
                    placeholder="Code promo"
                    value={promoCode}
                    onChange={(e) => setPromoCode(e.target.value)}
                    className="flex-1 px-3 py-2 border rounded-l-lg focus:outline-none focus:ring-2 focus:ring-blue-400"
                  />
                  <button
                    onClick={applyPromoCode}
                    className="bg-gray-600 text-white px-4 py-2 rounded-r-lg hover:bg-gray-700"
                  >
                    Appliquer
                  </button>
                </div>
              </div>

              <button className="w-full bg-green-600 text-white py-3 rounded-lg text-lg font-semibold hover:bg-green-700">
                Procéder au paiement
              </button>
              
              <p className="text-xs text-gray-500 mt-2 text-center">
                * Le paiement sera disponible prochainement
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

// Admin Panel Component
const AdminPanel = () => {
  const { user } = useAuth();
  const [activeTab, setActiveTab] = useState('products');
  const [products, setProducts] = useState([]);
  const [showAddProduct, setShowAddProduct] = useState(false);
  const [editingProduct, setEditingProduct] = useState(null);
  
  // Product filters
  const [filterCategory, setFilterCategory] = useState('');
  const [filterBrand, setFilterBrand] = useState('');
  const [filterStockStatus, setFilterStockStatus] = useState('');
  const [searchAdmin, setSearchAdmin] = useState('');
  
  // Promo codes state
  const [promoCodes, setPromoCodes] = useState([]);
  const [showAddPromo, setShowAddPromo] = useState(false);
  const [editingPromo, setEditingPromo] = useState(null);
  const [promoForm, setPromoForm] = useState({
    code: '',
    discount_percentage: ''
  });
  
  const [productForm, setProductForm] = useState({
    name: '',
    category: 'CPU',
    brand: '',
    price: '',
    description: '',
    stock_quantity: '',
    specifications: '',
    image_base64: ''
  });

  useEffect(() => {
    if (user && user.is_admin) {
      fetchProducts();
      if (activeTab === 'promos') {
        fetchPromoCodes();
      }
    }
  }, [user, activeTab]);

  const fetchProducts = async () => {
    try {
      const response = await axios.get(`${API}/products`);
      setProducts(response.data);
    } catch (error) {
      console.error('Erreur lors du chargement des produits:', error);
    }
  };

  const fetchPromoCodes = async () => {
    try {
      // Since there's no GET endpoint for promo codes, we'll need to manage them locally
      // or add the endpoint to the backend. For now, let's assume we have the endpoint
      const response = await axios.get(`${API}/admin/promo-codes`);
      setPromoCodes(response.data);
    } catch (error) {
      console.error('Erreur lors du chargement des codes promo:', error);
      // If endpoint doesn't exist, we'll work with local state
      setPromoCodes([]);
    }
  };

  // Get unique brands from products
  const getAvailableBrands = () => {
    const brands = new Set();
    products.forEach(product => brands.add(product.brand));
    return Array.from(brands).sort();
  };

  // Filter products based on selected filters
  const getFilteredProducts = () => {
    return products.filter(product => {
      const matchesCategory = !filterCategory || product.category === filterCategory;
      const matchesBrand = !filterBrand || product.brand === filterBrand;
      const matchesStock = !filterStockStatus || product.stock_status === filterStockStatus;
      const matchesSearch = !searchAdmin || 
        product.name.toLowerCase().includes(searchAdmin.toLowerCase()) ||
        product.brand.toLowerCase().includes(searchAdmin.toLowerCase()) ||
        product.description.toLowerCase().includes(searchAdmin.toLowerCase());
      
      return matchesCategory && matchesBrand && matchesStock && matchesSearch;
    });
  };

  const clearFilters = () => {
    setFilterCategory('');
    setFilterBrand('');
    setFilterStockStatus('');
    setSearchAdmin('');
  };

  const handlePromoSubmit = async (e) => {
    e.preventDefault();
    
    try {
      if (editingPromo) {
        // Update existing promo code
        await axios.put(`${API}/admin/promo-codes/${editingPromo.id}`, null, {
          params: {
            code: promoForm.code.toUpperCase(),
            discount_percentage: parseFloat(promoForm.discount_percentage)
          }
        });
        alert('Code promo modifié avec succès !');
      } else {
        // Create new promo code
        await axios.post(`${API}/admin/promo-codes`, null, {
          params: {
            code: promoForm.code.toUpperCase(),
            discount_percentage: parseFloat(promoForm.discount_percentage)
          }
        });
        alert('Code promo créé avec succès !');
      }
      
      resetPromoForm();
      fetchPromoCodes();
    } catch (error) {
      console.error('Erreur:', error);
      alert('Erreur lors de l\'opération');
    }
  };

  const resetPromoForm = () => {
    setPromoForm({ code: '', discount_percentage: '' });
    setShowAddPromo(false);
    setEditingPromo(null);
  };

  const editPromo = (promo) => {
    setPromoForm({
      code: promo.code,
      discount_percentage: promo.discount_percentage.toString()
    });
    setEditingPromo(promo);
    setShowAddPromo(true);
  };

  const deletePromo = async (promoId) => {
    if (!confirm('Êtes-vous sûr de vouloir supprimer ce code promo ?')) return;
    
    try {
      await axios.delete(`${API}/admin/promo-codes/${promoId}`);
      alert('Code promo supprimé avec succès !');
      fetchPromoCodes();
    } catch (error) {
      console.error('Erreur lors de la suppression:', error);
      alert('Erreur lors de la suppression');
    }
  };

  const togglePromoStatus = async (promoId, currentStatus) => {
    try {
      await axios.put(`${API}/admin/promo-codes/${promoId}/toggle`, null, {
        params: { active: !currentStatus }
      });
      alert(`Code promo ${!currentStatus ? 'activé' : 'désactivé'} avec succès !`);
      fetchPromoCodes();
    } catch (error) {
      console.error('Erreur:', error);
      alert('Erreur lors du changement de statut');
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    try {
      const formData = {
        ...productForm,
        price: parseFloat(productForm.price),
        stock_quantity: parseInt(productForm.stock_quantity),
        specifications: productForm.specifications ? JSON.parse(productForm.specifications) : {}
      };

      if (editingProduct) {
        await axios.put(`${API}/admin/products/${editingProduct.id}`, formData);
        alert('Produit modifié avec succès !');
      } else {
        await axios.post(`${API}/admin/products`, formData);
        alert('Produit ajouté avec succès !');
      }
      
      resetForm();
      fetchProducts();
    } catch (error) {
      console.error('Erreur:', error);
      alert('Erreur lors de l\'opération');
    }
  };

  const resetForm = () => {
    setProductForm({
      name: '',
      category: 'CPU',
      brand: '',
      price: '',
      description: '',
      stock_quantity: '',
      specifications: '',
      image_base64: ''
    });
    setShowAddProduct(false);
    setEditingProduct(null);
  };

  const editProduct = (product) => {
    setProductForm({
      name: product.name,
      category: product.category,
      brand: product.brand,
      price: product.price.toString(),
      description: product.description,
      stock_quantity: product.stock_quantity.toString(),
      specifications: JSON.stringify(product.specifications, null, 2),
      image_base64: product.image_base64 || ''
    });
    setEditingProduct(product);
    setShowAddProduct(true);
  };

  const deleteProduct = async (productId) => {
    if (!confirm('Êtes-vous sûr de vouloir supprimer ce produit ?')) return;
    
    try {
      await axios.delete(`${API}/admin/products/${productId}`);
      alert('Produit supprimé avec succès !');
      fetchProducts();
    } catch (error) {
      console.error('Erreur lors de la suppression:', error);
      alert('Erreur lors de la suppression');
    }
  };

  const handleImageUpload = (e) => {
    const file = e.target.files[0];
    if (file) {
      const reader = new FileReader();
      reader.onload = (e) => {
        const base64 = e.target.result.split(',')[1];
        setProductForm({ ...productForm, image_base64: base64 });
      };
      reader.readAsDataURL(file);
    }
  };

  if (!user || !user.is_admin) {
    return <div className="text-center py-8">Accès non autorisé</div>;
  }

  return (
    <div className="container mx-auto px-4 py-8">
      <h1 className="text-3xl font-bold mb-8">Panel Administrateur</h1>

      <div className="flex border-b mb-6">
        <button
          className={`px-4 py-2 ${activeTab === 'products' ? 'border-b-2 border-blue-600 text-blue-600' : 'text-gray-600'}`}
          onClick={() => setActiveTab('products')}
        >
          Gestion des produits
        </button>
        <button
          className={`px-4 py-2 ${activeTab === 'promos' ? 'border-b-2 border-blue-600 text-blue-600' : 'text-gray-600'}`}
          onClick={() => setActiveTab('promos')}
        >
          Codes promo
        </button>
      </div>

      {activeTab === 'products' && (
        <div>
          <div className="flex justify-between items-center mb-6">
            <h2 className="text-2xl font-semibold">Produits</h2>
            <button
              onClick={() => setShowAddProduct(true)}
              className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700"
            >
              Ajouter un produit
            </button>
          </div>

          {/* Filters Section */}
          <div className="bg-white p-4 rounded-lg shadow mb-6">
            <h3 className="text-lg font-semibold mb-4">Filtres</h3>
            <div className="grid md:grid-cols-4 gap-4">
              <div>
                <label className="block text-sm font-medium mb-1">Recherche</label>
                <input
                  type="text"
                  placeholder="Nom, marque, description..."
                  value={searchAdmin}
                  onChange={(e) => setSearchAdmin(e.target.value)}
                  className="w-full p-2 border rounded focus:outline-none focus:ring-2 focus:ring-blue-400"
                />
              </div>

              <div>
                <label className="block text-sm font-medium mb-1">Catégorie</label>
                <select
                  value={filterCategory}
                  onChange={(e) => setFilterCategory(e.target.value)}
                  className="w-full p-2 border rounded focus:outline-none focus:ring-2 focus:ring-blue-400"
                >
                  <option value="">Toutes les catégories</option>
                  {['CPU', 'GPU', 'RAM', 'MOTHERBOARD', 'STORAGE', 'PSU', 'CASE', 'COOLING'].map(cat => (
                    <option key={cat} value={cat}>{cat}</option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium mb-1">Marque</label>
                <select
                  value={filterBrand}
                  onChange={(e) => setFilterBrand(e.target.value)}
                  className="w-full p-2 border rounded focus:outline-none focus:ring-2 focus:ring-blue-400"
                >
                  <option value="">Toutes les marques</option>
                  {getAvailableBrands().map(brand => (
                    <option key={brand} value={brand}>{brand}</option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium mb-1">Statut Stock</label>
                <select
                  value={filterStockStatus}
                  onChange={(e) => setFilterStockStatus(e.target.value)}
                  className="w-full p-2 border rounded focus:outline-none focus:ring-2 focus:ring-blue-400"
                >
                  <option value="">Tous les statuts</option>
                  <option value="in_stock">En stock</option>
                  <option value="out_of_stock">Rupture de stock</option>
                  <option value="coming_soon">Bientôt disponible</option>
                </select>
              </div>
            </div>

            <div className="mt-4 flex space-x-2">
              <button
                onClick={clearFilters}
                className="bg-gray-500 text-white px-4 py-2 rounded hover:bg-gray-600"
              >
                Réinitialiser filtres
              </button>
              <span className="text-sm text-gray-600 self-center">
                {getFilteredProducts().length} produit(s) affiché(s) sur {products.length}
              </span>
            </div>
          </div>

          {/* Add/Edit Product Form */}
          {showAddProduct && (
            <div className="bg-white p-6 rounded-lg shadow mb-6">
              <h3 className="text-lg font-semibold mb-4">
                {editingProduct ? 'Modifier le produit' : 'Ajouter un nouveau produit'}
              </h3>
              
              <form onSubmit={handleSubmit} className="grid md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium mb-1">Nom</label>
                  <input
                    type="text"
                    value={productForm.name}
                    onChange={(e) => setProductForm({...productForm, name: e.target.value})}
                    className="w-full p-2 border rounded focus:outline-none focus:ring-2 focus:ring-blue-400"
                    required
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium mb-1">Catégorie</label>
                  <select
                    value={productForm.category}
                    onChange={(e) => setProductForm({...productForm, category: e.target.value})}
                    className="w-full p-2 border rounded focus:outline-none focus:ring-2 focus:ring-blue-400"
                  >
                    {['CPU', 'GPU', 'RAM', 'MOTHERBOARD', 'STORAGE', 'PSU', 'CASE', 'COOLING'].map(cat => (
                      <option key={cat} value={cat}>{cat}</option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium mb-1">Marque</label>
                  <input
                    type="text"
                    value={productForm.brand}
                    onChange={(e) => setProductForm({...productForm, brand: e.target.value})}
                    className="w-full p-2 border rounded focus:outline-none focus:ring-2 focus:ring-blue-400"
                    required
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium mb-1">Prix (MAD)</label>
                  <input
                    type="number"
                    step="0.01"
                    value={productForm.price}
                    onChange={(e) => setProductForm({...productForm, price: e.target.value})}
                    className="w-full p-2 border rounded focus:outline-none focus:ring-2 focus:ring-blue-400"
                    required
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium mb-1">Stock</label>
                  <input
                    type="number"
                    value={productForm.stock_quantity}
                    onChange={(e) => setProductForm({...productForm, stock_quantity: e.target.value})}
                    className="w-full p-2 border rounded focus:outline-none focus:ring-2 focus:ring-blue-400"
                    required
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium mb-1">Image</label>
                  <input
                    type="file"
                    accept="image/*"
                    onChange={handleImageUpload}
                    className="w-full p-2 border rounded focus:outline-none focus:ring-2 focus:ring-blue-400"
                  />
                </div>

                <div className="md:col-span-2">
                  <label className="block text-sm font-medium mb-1">Description</label>
                  <textarea
                    value={productForm.description}
                    onChange={(e) => setProductForm({...productForm, description: e.target.value})}
                    className="w-full p-2 border rounded focus:outline-none focus:ring-2 focus:ring-blue-400"
                    rows="3"
                    required
                  />
                </div>

                <div className="md:col-span-2">
                  <label className="block text-sm font-medium mb-1">Spécifications (JSON)</label>
                  <textarea
                    value={productForm.specifications}
                    onChange={(e) => setProductForm({...productForm, specifications: e.target.value})}
                    className="w-full p-2 border rounded focus:outline-none focus:ring-2 focus:ring-blue-400"
                    rows="4"
                    placeholder='{"socket": "AM4", "cores": 12, "threads": 24}'
                  />
                </div>

                <div className="md:col-span-2 flex space-x-4">
                  <button
                    type="submit"
                    className="bg-blue-600 text-white px-6 py-2 rounded hover:bg-blue-700"
                  >
                    {editingProduct ? 'Modifier' : 'Ajouter'}
                  </button>
                  <button
                    type="button"
                    onClick={resetForm}
                    className="bg-gray-600 text-white px-6 py-2 rounded hover:bg-gray-700"
                  >
                    Annuler
                  </button>
                </div>
              </form>
            </div>
          )}

          {/* Products List */}
          <div className="bg-white rounded-lg shadow overflow-hidden">
            <div className="overflow-x-auto">
              <table className="min-w-full">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Produit
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Catégorie
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Prix
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Stock
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Actions
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {getFilteredProducts().map(product => (
                    <tr key={product.id}>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div>
                          <div className="text-sm font-medium text-gray-900">{product.name}</div>
                          <div className="text-sm text-gray-500">{product.brand}</div>
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                          {product.category}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        {product.price} MAD
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                          product.stock_status === 'in_stock' 
                            ? 'bg-green-100 text-green-800' 
                            : 'bg-red-100 text-red-800'
                        }`}>
                          {product.stock_quantity} en stock
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium space-x-2">
                        <button
                          onClick={() => editProduct(product)}
                          className="text-blue-600 hover:text-blue-900"
                        >
                          Modifier
                        </button>
                        <button
                          onClick={() => deleteProduct(product.id)}
                          className="text-red-600 hover:text-red-900"
                        >
                          Supprimer
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {activeTab === 'promos' && (
        <div>
          <div className="flex justify-between items-center mb-6">
            <h2 className="text-2xl font-semibold">Codes Promo</h2>
            <button
              onClick={() => setShowAddPromo(true)}
              className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700"
            >
              Créer un code promo
            </button>
          </div>

          {/* Add/Edit Promo Form */}
          {showAddPromo && (
            <div className="bg-white p-6 rounded-lg shadow mb-6">
              <h3 className="text-lg font-semibold mb-4">
                {editingPromo ? 'Modifier le code promo' : 'Créer un nouveau code promo'}
              </h3>
              
              <form onSubmit={handlePromoSubmit} className="grid md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium mb-1">Code Promo</label>
                  <input
                    type="text"
                    placeholder="ex: GAMING10"
                    value={promoForm.code}
                    onChange={(e) => setPromoForm({...promoForm, code: e.target.value.toUpperCase()})}
                    className="w-full p-2 border rounded focus:outline-none focus:ring-2 focus:ring-blue-400"
                    required
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium mb-1">Réduction (%)</label>
                  <input
                    type="number"
                    min="1"
                    max="99"
                    step="0.1"
                    placeholder="ex: 10.5"
                    value={promoForm.discount_percentage}
                    onChange={(e) => setPromoForm({...promoForm, discount_percentage: e.target.value})}
                    className="w-full p-2 border rounded focus:outline-none focus:ring-2 focus:ring-blue-400"
                    required
                  />
                </div>

                <div className="md:col-span-2 flex space-x-4">
                  <button
                    type="submit"
                    className="bg-blue-600 text-white px-6 py-2 rounded hover:bg-blue-700"
                  >
                    {editingPromo ? 'Modifier' : 'Créer'}
                  </button>
                  <button
                    type="button"
                    onClick={resetPromoForm}
                    className="bg-gray-600 text-white px-6 py-2 rounded hover:bg-gray-700"
                  >
                    Annuler
                  </button>
                </div>
              </form>
            </div>
          )}

          {/* Promo Codes List */}
          <div className="bg-white rounded-lg shadow overflow-hidden">
            <div className="overflow-x-auto">
              <table className="min-w-full">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Code
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Réduction
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Statut
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Date de création
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Actions
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {promoCodes.map(promo => (
                    <tr key={promo.id}>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm font-medium text-gray-900">{promo.code}</div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        {promo.discount_percentage}%
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                          promo.active 
                            ? 'bg-green-100 text-green-800' 
                            : 'bg-red-100 text-red-800'
                        }`}>
                          {promo.active ? 'Actif' : 'Inactif'}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        {new Date(promo.created_at).toLocaleDateString('fr-FR')}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium space-x-2">
                        <button
                          onClick={() => editPromo(promo)}
                          className="text-blue-600 hover:text-blue-900"
                        >
                          Modifier
                        </button>
                        <button
                          onClick={() => togglePromoStatus(promo.id, promo.active)}
                          className={`${promo.active ? 'text-orange-600 hover:text-orange-900' : 'text-green-600 hover:text-green-900'}`}
                        >
                          {promo.active ? 'Désactiver' : 'Activer'}
                        </button>
                        <button
                          onClick={() => deletePromo(promo.id)}
                          className="text-red-600 hover:text-red-900"
                        >
                          Supprimer
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
              {promoCodes.length === 0 && (
                <div className="text-center py-8 text-gray-500">
                  Aucun code promo créé pour le moment
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

// Main App Component with Routing
const App = () => {
  const [currentPage, setCurrentPage] = useState(window.location.pathname);

  useEffect(() => {
    const handlePopState = () => {
      setCurrentPage(window.location.pathname);
    };
    
    window.addEventListener('popstate', handlePopState);
    return () => window.removeEventListener('popstate', handlePopState);
  }, []);

  const renderPage = () => {
    if (currentPage === '/') return <Homepage />;
    if (currentPage === '/login') return <Login />;
    if (currentPage === '/register') return <Register />;
    if (currentPage === '/admin-login') return <AdminLogin />;
    if (currentPage === '/products') return <Products />;
    if (currentPage.startsWith('/product/')) return <ProductDetail productId={currentPage.split('/')[2]} />;
    if (currentPage === '/configurator') return <PCConfigurator />;
    if (currentPage === '/cart') return <Cart />;
    if (currentPage === '/admin') return <AdminPanel />;
    
    return <div className="text-center py-8">Page non trouvée</div>;
  };

  return (
    <AuthProvider>
      <div className="min-h-screen bg-gray-50">
        <Header />
        <main>
          {renderPage()}
        </main>
        <footer className="bg-gray-800 text-white py-8">
          <div className="container mx-auto px-4 text-center">
            <p>&copy; 2025 INFOTECH.MA - Votre spécialiste en composants PC gaming</p>
          </div>
        </footer>
      </div>
    </AuthProvider>
  );
};

export default App;