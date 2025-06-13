// ==================== PACKAGE.JSON (Root) ====================
{
  "name": "freshness-optimization-app",
  "version": "1.0.0",
  "description": "Full-stack application for food freshness optimization",
  "main": "server/index.js",
  "scripts": {
    "dev": "concurrently \"npm run server\" \"npm run client\"",
    "server": "cd server && npm run dev",
    "client": "cd client && npm start",
    "build": "cd client && npm run build",
    "install-all": "npm install && cd server && npm install && cd ../client && npm install"
  },
  "keywords": ["freshness", "optimization", "sustainability", "retail"],
  "author": "Your Name",
  "license": "MIT",
  "devDependencies": {
    "concurrently": "^7.6.0"
  }
}

// ==================== SERVER PACKAGE.JSON ====================
// server/package.json
{
  "name": "freshness-server",
  "version": "1.0.0",
  "main": "index.js",
  "scripts": {
    "start": "node index.js",
    "dev": "nodemon index.js"
  },
  "dependencies": {
    "express": "^4.18.2",
    "mongoose": "^7.5.0",
    "cors": "^2.8.5",
    "multer": "^1.4.5-lts.1",
    "socket.io": "^4.7.2",
    "sharp": "^0.32.5",
    "dotenv": "^16.3.1",
    "bcryptjs": "^2.4.3",
    "jsonwebtoken": "^9.0.2",
    "node-cron": "^3.0.2"
  },
  "devDependencies": {
    "nodemon": "^3.0.1"
  }
}

// ==================== CLIENT PACKAGE.JSON ====================
// client/package.json
{
  "name": "freshness-client",
  "version": "1.0.0",
  "private": true,
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "react-router-dom": "^6.15.0",
    "socket.io-client": "^4.7.2",
    "recharts": "^2.8.0",
    "axios": "^1.5.0",
    "react-webcam": "^7.1.1",
    "react-toastify": "^9.1.3",
    "lucide-react": "^0.263.1",
    "@headlessui/react": "^1.7.17"
  },
  "scripts": {
    "start": "react-scripts start",
    "build": "react-scripts build",
    "test": "react-scripts test",
    "eject": "react-scripts eject"
  },
  "devDependencies": {
    "react-scripts": "5.0.1",
    "tailwindcss": "^3.3.3",
    "autoprefixer": "^10.4.15",
    "postcss": "^8.4.29"
  },
  "browserslist": {
    "production": [">0.2%", "not dead", "not op_mini all"],
    "development": ["last 1 chrome version", "last 1 firefox version", "last 1 safari version"]
  },
  "proxy": "http://localhost:5000"
}

// ==================== SERVER ENTRY POINT ====================
// server/index.js
const express = require('express');
const mongoose = require('mongoose');
const cors = require('cors');
const http = require('http');
const socketIo = require('socket.io');
const multer = require('multer');
const path = require('path');
require('dotenv').config();

const app = express();
const server = http.createServer(app);
const io = socketIo(server, {
  cors: {
    origin: "http://localhost:3000",
    methods: ["GET", "POST"]
  }
});

// Middleware
app.use(cors());
app.use(express.json());
app.use('/uploads', express.static('uploads'));

// MongoDB Connection
mongoose.connect(process.env.MONGODB_URI || 'mongodb://localhost:27017/freshness-db', {
  useNewUrlParser: true,
  useUnifiedTopology: true,
});

// Models
const Product = require('./models/Product');
const FreshnessHistory = require('./models/FreshnessHistory');
const Analytics = require('./models/Analytics');

// Multer configuration for file uploads
const storage = multer.diskStorage({
  destination: (req, file, cb) => {
    cb(null, 'uploads/');
  },
  filename: (req, file, cb) => {
    cb(null, Date.now() + '-' + file.originalname);
  }
});
const upload = multer({ storage: storage });

// Socket.io connection handling
io.on('connection', (socket) => {
  console.log('User connected:', socket.id);
  
  socket.on('disconnect', () => {
    console.log('User disconnected:', socket.id);
  });
});

// Routes
app.use('/api/products', require('./routes/products'));
app.use('/api/analytics', require('./routes/analytics'));
app.use('/api/freshness', require('./routes/freshness'));

// Image analysis endpoint
app.post('/api/analyze-image', upload.single('image'), async (req, res) => {
  try {
    if (!req.file) {
      return res.status(400).json({ error: 'No image uploaded' });
    }

    const imagePath = req.file.path;
    const productType = req.body.productType || 'unknown';
    
    // Simulate freshness analysis (replace with actual AI/ML service)
    const freshnessScore = await analyzeFreshness(imagePath, productType);
    
    // Update product if productId provided
    if (req.body.productId) {
      await Product.findByIdAndUpdate(req.body.productId, {
        freshnessScore: freshnessScore,
        lastScanned: new Date(),
        imageUrl: `/uploads/${req.file.filename}`
      });
      
      // Save to history
      await new FreshnessHistory({
        productId: req.body.productId,
        freshnessScore: freshnessScore,
        imageUrl: `/uploads/${req.file.filename}`,
        recordedAt: new Date()
      }).save();
      
      // Emit real-time update
      io.emit('freshnessUpdate', {
        productId: req.body.productId,
        freshnessScore: freshnessScore
      });
    }
    
    res.json({
      freshnessScore: freshnessScore,
      confidence: Math.random() * 0.3 + 0.7, // Simulated confidence
      imageUrl: `/uploads/${req.file.filename}`,
      analysis: {
        colorHealth: freshnessScore > 70 ? 'Good' : 'Declining',
        textureHealth: freshnessScore > 60 ? 'Firm' : 'Soft',
        overallCondition: freshnessScore > 80 ? 'Excellent' : freshnessScore > 60 ? 'Good' : 'Fair'
      }
    });
  } catch (error) {
    console.error('Image analysis error:', error);
    res.status(500).json({ error: 'Failed to analyze image' });
  }
});

// Freshness analysis function (simplified simulation)
async function analyzeFreshness(imagePath, productType) {
  // This is a simplified simulation - replace with actual AI/ML analysis
  const sharp = require('sharp');
  
  try {
    const stats = await sharp(imagePath).stats();
    
    // Simple analysis based on color statistics
    let freshnessScore = 85; // Base score
    
    // Analyze dominant colors (simplified)
    if (stats.dominant) {
      // If image has lots of brown/dark colors, reduce freshness
      if (stats.dominant.r < 100 && stats.dominant.g < 100) {
        freshnessScore -= 20;
      }
    }
    
    // Add some randomness to simulate real analysis
    freshnessScore += (Math.random() - 0.5) * 20;
    
    return Math.max(0, Math.min(100, Math.round(freshnessScore)));
  } catch (error) {
    console.error('Sharp analysis error:', error);
    return Math.floor(Math.random() * 40) + 60; // Fallback random score
  }
}

const PORT = process.env.PORT || 5000;
server.listen(PORT, () => {
  console.log(`Server running on port ${PORT}`);
});

// ==================== MONGODB MODELS ====================
// server/models/Product.js
const mongoose = require('mongoose');

const productSchema = new mongoose.Schema({
  name: {
    type: String,
    required: true
  },
  category: {
    type: String,
    required: true,
    enum: ['fruits', 'vegetables', 'dairy', 'meat', 'bakery', 'other']
  },
  basePrice: {
    type: Number,
    required: true
  },
  currentPrice: {
    type: Number,
    required: true
  },
  freshnessScore: {
    type: Number,
    default: 100,
    min: 0,
    max: 100
  },
  imageUrl: {
    type: String,
    default: ''
  },
  expiryDate: {
    type: Date,
    required: true
  },
  lastScanned: {
    type: Date,
    default: Date.now
  },
  location: {
    aisle: String,
    shelf: String,
    position: String
  },
  supplier: {
    name: String,
    id: String
  },
  isActive: {
    type: Boolean,
    default: true
  }
}, {
  timestamps: true
});

// Calculate dynamic pricing based on freshness
productSchema.methods.calculateOptimalPrice = function() {
  const daysToExpiry = Math.ceil((this.expiryDate - new Date()) / (1000 * 60 * 60 * 24));
  let multiplier = 1;
  
  if (this.freshnessScore > 90) multiplier = 1.0;
  else if (this.freshnessScore > 70) multiplier = 0.95;
  else if (this.freshnessScore > 50) multiplier = 0.85;
  else if (this.freshnessScore > 30) multiplier = 0.70;
  else multiplier = 0.50;
  
  // Factor in days to expiry
  if (daysToExpiry <= 1) multiplier *= 0.7;
  else if (daysToExpiry <= 3) multiplier *= 0.85;
  
  return Math.round(this.basePrice * multiplier * 100) / 100;
};

module.exports = mongoose.model('Product', productSchema);

// server/models/FreshnessHistory.js
const mongoose = require('mongoose');

const freshnessHistorySchema = new mongoose.Schema({
  productId: {
    type: mongoose.Schema.Types.ObjectId,
    ref: 'Product',
    required: true
  },
  freshnessScore: {
    type: Number,
    required: true,
    min: 0,
    max: 100
  },
  temperature: {
    type: Number,
    default: null
  },
  humidity: {
    type: Number,
    default: null
  },
  imageUrl: {
    type: String,
    default: ''
  },
  recordedAt: {
    type: Date,
    default: Date.now
  },
  notes: {
    type: String,
    default: ''
  }
});

module.exports = mongoose.model('FreshnessHistory', freshnessHistorySchema);

// server/models/Analytics.js
const mongoose = require('mongoose');

const analyticsSchema = new mongoose.Schema({
  date: {
    type: Date,
    required: true,
    unique: true
  },
  wasteReduction: {
    totalWastePrevented: { type: Number, default: 0 },
    costSavings: { type: Number, default: 0 },
    co2Saved: { type: Number, default: 0 }
  },
  financialImpact: {
    revenueIncrease: { type: Number, default: 0 },
    profitIncrease: { type: Number, default: 0 },
    inventoryTurnover: { type: Number, default: 0 }
  },
  operationalMetrics: {
    productsScanned: { type: Number, default: 0 },
    priceAdjustments: { type: Number, default: 0 },
    averageFreshnessScore: { type: Number, default: 0 }
  }
}, {
  timestamps: true
});

module.exports = mongoose.model('Analytics', analyticsSchema);

// ==================== SERVER ROUTES ====================
// server/routes/products.js
const express = require('express');
const router = express.Router();
const Product = require('../models/Product');

// Get all products
router.get('/', async (req, res) => {
  try {
    const products = await Product.find({ isActive: true }).sort({ createdAt: -1 });
    res.json(products);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// Get single product
router.get('/:id', async (req, res) => {
  try {
    const product = await Product.findById(req.params.id);
    if (!product) {
      return res.status(404).json({ error: 'Product not found' });
    }
    res.json(product);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// Create new product
router.post('/', async (req, res) => {
  try {
    const product = new Product({
      ...req.body,
      currentPrice: req.body.basePrice
    });
    await product.save();
    res.status(201).json(product);
  } catch (error) {
    res.status(400).json({ error: error.message });
  }
});

// Update product
router.put('/:id', async (req, res) => {
  try {
    const product = await Product.findByIdAndUpdate(
      req.params.id,
      req.body,
      { new: true, runValidators: true }
    );
    if (!product) {
      return res.status(404).json({ error: 'Product not found' });
    }
    res.json(product);
  } catch (error) {
    res.status(400).json({ error: error.message });
  }
});

// Update product price
router.put('/:id/price', async (req, res) => {
  try {
    const { price } = req.body;
    const product = await Product.findByIdAndUpdate(
      req.params.id,
      { currentPrice: price },
      { new: true }
    );
    if (!product) {
      return res.status(404).json({ error: 'Product not found' });
    }
    res.json(product);
  } catch (error) {
    res.status(400).json({ error: error.message });
  }
});

// Calculate optimal pricing for all products
router.post('/optimize-pricing', async (req, res) => {
  try {
    const products = await Product.find({ isActive: true });
    const updates = [];
    
    for (let product of products) {
      const optimalPrice = product.calculateOptimalPrice();
      if (optimalPrice !== product.currentPrice) {
        product.currentPrice = optimalPrice;
        await product.save();
        updates.push({
          productId: product._id,
          name: product.name,
          oldPrice: product.currentPrice,
          newPrice: optimalPrice
        });
      }
    }
    
    res.json({
      message: `Updated pricing for ${updates.length} products`,
      updates: updates
    });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// Delete product
router.delete('/:id', async (req, res) => {
  try {
    const product = await Product.findByIdAndUpdate(
      req.params.id,
      { isActive: false },
      { new: true }
    );
    if (!product) {
      return res.status(404).json({ error: 'Product not found' });
    }
    res.json({ message: 'Product deleted successfully' });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

module.exports = router;

// server/routes/analytics.js
const express = require('express');
const router = express.Router();
const Product = require('../models/Product');
const FreshnessHistory = require('../models/FreshnessHistory');
const Analytics = require('../models/Analytics');

// Get waste reduction analytics
router.get('/waste', async (req, res) => {
  try {
    const { startDate, endDate } = req.query;
    
    // Calculate waste reduction metrics
    const products = await Product.find({ isActive: true });
    const totalProducts = products.length;
    const freshProducts = products.filter(p => p.freshnessScore > 70).length;
    const wasteReduction = ((freshProducts / totalProducts) * 100).toFixed(1);
    
    // Simulate historical data
    const wasteData = [];
    for (let i = 30; i >= 0; i--) {
      const date = new Date();
      date.setDate(date.getDate() - i);
      wasteData.push({
        date: date.toISOString().split('T')[0],
        wasteReduced: Math.random() * 50 + 20,
        costSaved: Math.random() * 1000 + 500
      });
    }
    
    res.json({
      summary: {
        totalWasteReduction: wasteReduction,
        costSavings: 25000,
        co2Saved: 1500,
        itemsSaved: 450
      },
      historicalData: wasteData
    });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// Get sustainability metrics
router.get('/sustainability', async (req, res) => {
  try {
    const products = await Product.find({ isActive: true });
    
    // Calculate environmental impact
    const totalProducts = products.length;
    const averageFreshness = products.reduce((sum, p) => sum + p.freshnessScore, 0) / totalProducts;
    
    const sustainabilityData = {
      carbonFootprint: {
        reduced: 2.5, // tons of CO2
        percentage: 15
      },
      waterSaved: {
        gallons: 5000,
        percentage: 12
      },
      energySaved: {
        kwh: 1200,
        percentage: 8
      },
      wasteToLandfill: {
        poundsReduced: 3500,
        percentage: 35
      }
    };
    
    res.json(sustainabilityData);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// Get financial impact analytics
router.get('/financial', async (req, res) => {
  try {
    const products = await Product.find({ isActive: true });
    
    // Calculate financial metrics
    const totalRevenue = products.reduce((sum, p) => sum + p.currentPrice, 0);
    const potentialRevenue = products.reduce((sum, p) => sum + p.basePrice, 0);
    
    const financialData = {
      revenueOptimization: {
        current: totalRevenue,
        potential: potentialRevenue,
        improvement: ((potentialRevenue - totalRevenue) / totalRevenue * 100).toFixed(1)
      },
      costSavings: {
        wasteReduction: 15000,
        inventoryOptimization: 8000,
        staffEfficiency: 5000
      },
      profitMargins: {
        before: 12.5,
        after: 18.2,
        improvement: 5.7
      }
    };
    
    res.json(financialData);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// Get dashboard summary
router.get('/dashboard', async (req, res) => {
  try {
    const products = await Product.find({ isActive: true });
    const totalProducts = products.length;
    
    const summary = {
      totalProducts: totalProducts,
      averageFreshness: (products.reduce((sum, p) => sum + p.freshnessScore, 0) / totalProducts).toFixed(1),
      productsNeedingAttention: products.filter(p => p.freshnessScore < 50).length,
      totalValueAtRisk: products
        .filter(p => p.freshnessScore < 50)
        .reduce((sum, p) => sum + p.currentPrice, 0)
        .toFixed(2),
      wasteReductionToday: 12.5,
      costSavingsToday: 450
    };
    
    res.json(summary);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

module.exports = router;

// server/routes/freshness.js
const express = require('express');
const router = express.Router();
const FreshnessHistory = require('../models/FreshnessHistory');
const Product = require('../models/Product');

// Get freshness history for a product
router.get('/history/:productId', async (req, res) => {
  try {
    const history = await FreshnessHistory.find({ productId: req.params.productId })
      .sort({ recordedAt: -1 })
      .limit(50);
    res.json(history);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// Get freshness trends
router.get('/trends', async (req, res) => {
  try {
    const { category, days = 7 } = req.query;
    
    const startDate = new Date();
    startDate.setDate(startDate.getDate() - parseInt(days));
    
    let productFilter = { isActive: true };
    if (category && category !== 'all') {
      productFilter.category = category;
    }
    
    const products = await Product.find(productFilter);
    const productIds = products.map(p => p._id);
    
    const trends = await FreshnessHistory.aggregate([
      {
        $match: {
          productId: { $in: productIds },
          recordedAt: { $gte: startDate }
        }
      },
      {
        $group: {
          _id: {
            $dateToString: { format: "%Y-%m-%d", date: "$recordedAt" }
          },
          averageFreshness: { $avg: "$freshnessScore" },
          count: { $sum: 1 }
        }
      },
      {
        $sort: { "_id": 1 }
      }
    ]);
    
    res.json(trends);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

module.exports = router;

// ==================== REACT APP ENTRY POINT ====================
// client/src/index.js
import React from 'react';
import ReactDOM from 'react-dom/client';
import './index.css';
import App from './App';

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);

// client/src/App.js
import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { ToastContainer } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';

import Layout from './components/Layout';
import Dashboard from './pages/Dashboard';
import Products from './pages/Products';
import Analytics from './pages/Analytics';
import Camera from './pages/Camera';
import Pricing from './pages/Pricing';

function App() {
  return (
    <Router>
      <div className="App">
        <Layout>
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/products" element={<Products />} />
            <Route path="/analytics" element={<Analytics />} />
            <Route path="/camera" element={<Camera />} />
            <Route path="/pricing" element={<Pricing />} />
          </Routes>
        </Layout>
        <ToastContainer
          position="top-right"
          autoClose={3000}
          hideProgressBar={false}
          newestOnTop
          closeOnClick
          rtl={false}
          pauseOnFocusLoss
          draggable
          pauseOnHover
        />
      </div>
    </Router>
  );
}

export default App;

// ==================== REACT COMPONENTS ====================
// client/src/components/Layout.js
import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { 
  Home, 
  Package, 
  BarChart3, 
  Camera, 
  DollarSign,
  Leaf,
  Bell
} from 'lucide-react';

const Layout = ({ children }) => {
  const location = useLocation();
  
  const navigation = [
    { name: 'Dashboard', href: '/', icon: Home },
    { name: 'Products', href: '/products', icon: Package },
    { name: 'Analytics', href: '/analytics', icon: BarChart3 },
    { name: 'Camera', href: '/camera', icon: Camera },
    { name: 'Pricing', href: '/pricing', icon: DollarSign },
  ];
  
  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center">
              <Leaf className="h-8 w-8 text-green-600" />
              <h1 className="ml-2 text-xl font-bold text-gray-900">
                FreshOptimize
              </h1>
            </div>
            <div className="flex items-center space-x-4">
              <Bell className="h-6 w-6 text-gray-400" />
              <div className="w-8 h-8 bg-green-500 rounded-full flex items-center justify-center">
                <span className="text-white text-sm font-medium">U</span>
              </div>
            </div>
          </div>
        </div>
      </header>
      
      <div className="flex">
        {/* Sidebar */}
        <nav className="w-64 bg-white shadow-sm min-h-screen">
          <div className="p-4">
            <ul className="space-y-2">
              {navigation.map((item) => {
                const Icon = item.icon;
                const isActive = location.pathname === item.href;
                
                return (
                  <li key={item.name}>
                    <Link
                      to={item.href}
                      className={`flex items-center px-4 py-2 text-sm font-medium rounded-md transition-colors ${
                        isActive
                          ? 'bg-green-100 text-green-700'
                          : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900'
                      }`}
                    >
                      <Icon className="mr-3 h-5 w-5" />
                      {item.name}
                    </Link>
                  </li>
                );
              })}
            </ul>
          </div>
        </nav>
        
        {/* Main Content */}
        <main className="flex-1 p-8">
          {children}
        </main>
      </div>
    </div>
  );
};

export default Layout;

// client/src/pages/Dashboard.js
import React, { useState, useEffect } from 'react';
import { 
  TrendingUp, 
  TrendingDown, 
  Package, 
  AlertTriangle,
  DollarSign,
  Leaf
} from 'lucide-react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts';
import axios from 'axios';
import io from 'socket.io-client';

const Dashboard = () => {
  const [dashboardData, setDashboardData] = useState(null);
  const [wasteData, setWasteData] = useState([]);
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(true);
  
  useEffect(() => {
    fetchDashboardData();
    fetchProducts();
    
    // Setup Socket.io for real-time updates
    const socket = io('http://localhost:5000');
    socket.on('freshnessUpdate', (data) => {
      setProducts(prev => 
        prev.map(p => 
          p._id === data.productId 
            ? { ...p, freshnessScore: data.freshnessScore }
            : p
        )
      );
    });
    
    return () => socket.disconnect();
  }, []);
  
  const fetchDashboardData = async () => {
    try {
      const [dashboardRes, wasteRes] = await Promise.all([
        axios.get('/api/analytics/dashboard'),
        axios.get('/api/analytics/waste')
      ]);
      
      setDashboardData(dashboardRes.data);
      setWasteData(wasteRes.data.historicalData);
    } catch (error) {
      console.error('Error fetching dashboard data:', error);
    }
  };
  
  const fetchProducts = async () => {
    try {
      const response = await axios.get('/api/products');
      setProducts(response.data);
      setLoading(false);
    } catch (error) {
      console.error('Error fetching products:', error);
      setLoading(false);
    }
  };
  
 // Continuing from Dashboard.js freshnessDistribution...

  const freshnessDistribution = [
    { name: 'Excellent (90-100)', value: products.filter(p => p.freshnessScore >= 90).length, color: '#10B981' },
    { name: 'Good (70-89)', value: products.filter(p => p.freshnessScore >= 70 && p.freshnessScore < 90).length, color: '#F59E0B' },
    { name: 'Fair (50-69)', value: products.filter(p => p.freshnessScore >= 50 && p.freshnessScore < 70).length, color: '#F97316' },
    { name: 'Poor (<50)', value: products.filter(p => p.freshnessScore < 50).length, color: '#EF4444' }
  ];

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-green-600"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold text-gray-900">Dashboard</h1>
        <div className="text-sm text-gray-500">
          Last updated: {new Date().toLocaleTimeString()}
        </div>
      </div>

      {/* Key Metrics */}
      {dashboardData && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <div className="bg-white p-6 rounded-lg shadow">
            <div className="flex items-center">
              <Package className="h-8 w-8 text-blue-600" />
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-500">Total Products</p>
                <p className="text-2xl font-bold text-gray-900">{dashboardData.totalProducts}</p>
              </div>
            </div>
          </div>

          <div className="bg-white p-6 rounded-lg shadow">
            <div className="flex items-center">
              <TrendingUp className="h-8 w-8 text-green-600" />
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-500">Avg Freshness</p>
                <p className="text-2xl font-bold text-gray-900">{dashboardData.averageFreshness}%</p>
              </div>
            </div>
          </div>

          <div className="bg-white p-6 rounded-lg shadow">
            <div className="flex items-center">
              <AlertTriangle className="h-8 w-8 text-orange-600" />
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-500">Need Attention</p>
                <p className="text-2xl font-bold text-gray-900">{dashboardData.productsNeedingAttention}</p>
              </div>
            </div>
          </div>

          <div className="bg-white p-6 rounded-lg shadow">
            <div className="flex items-center">
              <DollarSign className="h-8 w-8 text-green-600" />
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-500">Cost Savings Today</p>
                <p className="text-2xl font-bold text-gray-900">${dashboardData.costSavingsToday}</p>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Waste Reduction Trend */}
        <div className="bg-white p-6 rounded-lg shadow">
          <h3 className="text-lg font-medium text-gray-900 mb-4">Waste Reduction Trend</h3>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={wasteData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="date" />
              <YAxis />
              <Tooltip />
              <Line type="monotone" dataKey="wasteReduced" stroke="#10B981" strokeWidth={2} />
            </LineChart>
          </ResponsiveContainer>
        </div>

        {/* Freshness Distribution */}
        <div className="bg-white p-6 rounded-lg shadow">
          <h3 className="text-lg font-medium text-gray-900 mb-4">Freshness Distribution</h3>
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={freshnessDistribution}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                outerRadius={80}
                fill="#8884d8"
                dataKey="value"
              >
                {freshnessDistribution.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.color} />
                ))}
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Recent Products */}
      <div className="bg-white rounded-lg shadow">
        <div className="px-6 py-4 border-b border-gray-200">
          <h3 className="text-lg font-medium text-gray-900">Recent Products</h3>
        </div>
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Product
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Category
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Freshness
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Price
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Status
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {products.slice(0, 5).map((product) => (
                <tr key={product._id}>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="text-sm font-medium text-gray-900">{product.name}</div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                      {product.category}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="flex items-center">
                      <div className="text-sm text-gray-900">{product.freshnessScore}%</div>
                      <div className="ml-2 w-16 bg-gray-200 rounded-full h-2">
                        <div 
                          className={`h-2 rounded-full ${
                            product.freshnessScore >= 70 ? 'bg-green-500' : 
                            product.freshnessScore >= 50 ? 'bg-yellow-500' : 'bg-red-500'
                          }`}
                          style={{ width: `${product.freshnessScore}%` }}
                        ></div>
                      </div>
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    ${product.currentPrice}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                      product.freshnessScore >= 70 ? 'bg-green-100 text-green-800' :
                      product.freshnessScore >= 50 ? 'bg-yellow-100 text-yellow-800' :
                      'bg-red-100 text-red-800'
                    }`}>
                      {product.freshnessScore >= 70 ? 'Good' : 
                       product.freshnessScore >= 50 ? 'Fair' : 'Needs Attention'}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;

// ==================== PRODUCTS PAGE ====================
// client/src/pages/Products.js
import React, { useState, useEffect } from 'react';
import { Plus, Search, Filter, Edit, Trash2, Eye } from 'lucide-react';
import axios from 'axios';
import { toast } from 'react-toastify';
import ProductModal from '../components/ProductModal';

const Products = () => {
  const [products, setProducts] = useState([]);
  const [filteredProducts, setFilteredProducts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('all');
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [selectedProduct, setSelectedProduct] = useState(null);

  const categories = ['all', 'fruits', 'vegetables', 'dairy', 'meat', 'bakery', 'other'];

  useEffect(() => {
    fetchProducts();
  }, []);

  useEffect(() => {
    filterProducts();
  }, [products, searchTerm, selectedCategory]);

  const fetchProducts = async () => {
    try {
      const response = await axios.get('/api/products');
      setProducts(response.data);
      setLoading(false);
    } catch (error) {
      console.error('Error fetching products:', error);
      toast.error('Failed to fetch products');
      setLoading(false);
    }
  };

  const filterProducts = () => {
    let filtered = products;

    if (searchTerm) {
      filtered = filtered.filter(product =>
        product.name.toLowerCase().includes(searchTerm.toLowerCase())
      );
    }

    if (selectedCategory !== 'all') {
      filtered = filtered.filter(product => product.category === selectedCategory);
    }

    setFilteredProducts(filtered);
  };

  const handleCreateProduct = () => {
    setSelectedProduct(null);
    setIsModalOpen(true);
  };

  const handleEditProduct = (product) => {
    setSelectedProduct(product);
    setIsModalOpen(true);
  };

  const handleDeleteProduct = async (productId) => {
    if (window.confirm('Are you sure you want to delete this product?')) {
      try {
        await axios.delete(`/api/products/${productId}`);
        toast.success('Product deleted successfully');
        fetchProducts();
      } catch (error) {
        console.error('Error deleting product:', error);
        toast.error('Failed to delete product');
      }
    }
  };

  const handleModalSubmit = async (productData) => {
    try {
      if (selectedProduct) {
        await axios.put(`/api/products/${selectedProduct._id}`, productData);
        toast.success('Product updated successfully');
      } else {
        await axios.post('/api/products', productData);
        toast.success('Product created successfully');
      }
      setIsModalOpen(false);
      fetchProducts();
    } catch (error) {
      console.error('Error saving product:', error);
      toast.error('Failed to save product');
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-green-600"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold text-gray-900">Products</h1>
        <button
          onClick={handleCreateProduct}
          className="inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-green-600 hover:bg-green-700"
        >
          <Plus className="h-4 w-4 mr-2" />
          Add Product
        </button>
      </div>

      {/* Filters */}
      <div className="bg-white p-4 rounded-lg shadow">
        <div className="flex flex-col sm:flex-row gap-4">
          <div className="flex-1">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
              <input
                type="text"
                placeholder="Search products..."
                className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-md focus:ring-green-500 focus:border-green-500"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
              />
            </div>
          </div>
          <div>
            <select
              className="px-4 py-2 border border-gray-300 rounded-md focus:ring-green-500 focus:border-green-500"
              value={selectedCategory}
              onChange={(e) => setSelectedCategory(e.target.value)}
            >
              {categories.map(category => (
                <option key={category} value={category}>
                  {category === 'all' ? 'All Categories' : category.charAt(0).toUpperCase() + category.slice(1)}
                </option>
              ))}
            </select>
          </div>
        </div>
      </div>

      {/* Products Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
        {filteredProducts.map((product) => (
          <div key={product._id} className="bg-white rounded-lg shadow-md overflow-hidden">
            <div className="relative">
              {product.imageUrl ? (
                <img 
                  src={`http://localhost:5000${product.imageUrl}`} 
                  alt={product.name}
                  className="w-full h-48 object-cover"
                />
              ) : (
                <div className="w-full h-48 bg-gray-200 flex items-center justify-center">
                  <Package className="h-16 w-16 text-gray-400" />
                </div>
              )}
              <div className="absolute top-2 right-2">
                <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${
                  product.freshnessScore >= 70 ? 'bg-green-100 text-green-800' :
                  product.freshnessScore >= 50 ? 'bg-yellow-100 text-yellow-800' :
                  'bg-red-100 text-red-800'
                }`}>
                  {product.freshnessScore}%
                </span>
              </div>
            </div>
            
            <div className="p-4">
              <h3 className="text-lg font-semibold text-gray-900 mb-2">{product.name}</h3>
              <p className="text-sm text-gray-600 mb-2 capitalize">{product.category}</p>
              
              <div className="flex justify-between items-center mb-3">
                <span className="text-lg font-bold text-green-600">${product.currentPrice}</span>
                {product.currentPrice !== product.basePrice && (
                  <span className="text-sm text-gray-500 line-through">${product.basePrice}</span>
                )}
              </div>
              
              <div className="mb-3">
                <div className="flex justify-between text-sm text-gray-600 mb-1">
                  <span>Freshness</span>
                  <span>{product.freshnessScore}%</span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div 
                    className={`h-2 rounded-full ${
                      product.freshnessScore >= 70 ? 'bg-green-500' : 
                      product.freshnessScore >= 50 ? 'bg-yellow-500' : 'bg-red-500'
                    }`}
                    style={{ width: `${product.freshnessScore}%` }}
                  ></div>
                </div>
              </div>
              
              <div className="flex justify-between items-center">
                <span className="text-xs text-gray-500">
                  Expires: {new Date(product.expiryDate).toLocaleDateString()}
                </span>
                <div className="flex space-x-2">
                  <button
                    onClick={() => handleEditProduct(product)}
                    className="p-1 text-blue-600 hover:text-blue-800"
                  >
                    <Edit className="h-4 w-4" />
                  </button>
                  <button
                    onClick={() => handleDeleteProduct(product._id)}
                    className="p-1 text-red-600 hover:text-red-800"
                  >
                    <Trash2 className="h-4 w-4" />
                  </button>
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>

      {filteredProducts.length === 0 && (
        <div className="text-center py-12">
          <Package className="mx-auto h-12 w-12 text-gray-400" />
          <h3 className="mt-2 text-sm font-medium text-gray-900">No products found</h3>
          <p className="mt-1 text-sm text-gray-500">
            {searchTerm || selectedCategory !== 'all' 
              ? 'Try adjusting your search or filter criteria.'
              : 'Get started by adding your first product.'
            }
          </p>
        </div>
      )}

      {/* Product Modal */}
      <ProductModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        onSubmit={handleModalSubmit}
        product={selectedProduct}
      />
    </div>
  );
};

export default Products;

// ==================== PRODUCT MODAL COMPONENT ====================
// client/src/components/ProductModal.js
import React, { useState, useEffect } from 'react';
import { X } from 'lucide-react';

const ProductModal = ({ isOpen, onClose, onSubmit, product }) => {
  const [formData, setFormData] = useState({
    name: '',
    category: 'fruits',
    basePrice: '',
    expiryDate: '',
    location: {
      aisle: '',
      shelf: '',
      position: ''
    },
    supplier: {
      name: '',
      id: ''
    }
  });

  useEffect(() => {
    if (product) {
      setFormData({
        name: product.name || '',
        category: product.category || 'fruits',
        basePrice: product.basePrice || '',
        expiryDate: product.expiryDate ? new Date(product.expiryDate).toISOString().split('T')[0] : '',
        location: {
          aisle: product.location?.aisle || '',
          shelf: product.location?.shelf || '',
          position: product.location?.position || ''
        },
        supplier: {
          name: product.supplier?.name || '',
          id: product.supplier?.id || ''
        }
      });
    } else {
      setFormData({
        name: '',
        category: 'fruits',
        basePrice: '',
        expiryDate: '',
        location: {
          aisle: '',
          shelf: '',
          position: ''
        },
        supplier: {
          name: '',
          id: ''
        }
      });
    }
  }, [product, isOpen]);

  const handleSubmit = (e) => {
    e.preventDefault();
    onSubmit(formData);
  };

  const handleChange = (e) => {
    const { name, value } = e.target;
    if (name.includes('.')) {
      const [parent, child] = name.split('.');
      setFormData(prev => ({
        ...prev,
        [parent]: {
          ...prev[parent],
          [child]: value
        }
      }));
    } else {
      setFormData(prev => ({
        ...prev,
        [name]: value
      }));
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
      <div className="relative top-20 mx-auto p-5 border w-full max-w-2xl shadow-lg rounded-md bg-white">
        <div className="flex justify-between items-center mb-4">
          <h3 className="text-lg font-medium text-gray-900">
            {product ? 'Edit Product' : 'Add New Product'}
          </h3>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600"
          >
            <X className="h-6 w-6" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700">Name</label>
              <input
                type="text"
                name="name"
                required
                className="mt-1 block w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-green-500 focus:border-green-500"
                value={formData.name}
                onChange={handleChange}
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700">Category</label>
              <select
                name="category"
                required
                className="mt-1 block w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-green-500 focus:border-green-500"
                value={formData.category}
                onChange={handleChange}
              >
                <option value="fruits">Fruits</option>
                <option value="vegetables">Vegetables</option>
                <option value="dairy">Dairy</option>
                <option value="meat">Meat</option>
                <option value="bakery">Bakery</option>
                <option value="other">Other</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700">Base Price ($)</label>
              <input
                type="number"
                name="basePrice"
                step="0.01"
                required
                className="mt-1 block w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-green-500 focus:border-green-500"
                value={formData.basePrice}
                onChange={handleChange}
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700">Expiry Date</label>
              <input
                type="date"
                name="expiryDate"
                required
                className="mt-1 block w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-green-500 focus:border-green-500"
                value={formData.expiryDate}
                onChange={handleChange}
              />
            </div>
          </div>

          <div className="border-t pt-4">
            <h4 className="text-md font-medium text-gray-900 mb-2">Location</h4>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700">Aisle</label>
                <input
                  type="text"
                  name="location.aisle"
                  className="mt-1 block w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-green-500 focus:border-green-500"
                  value={formData.location.aisle}
                  onChange={handleChange}
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700">Shelf</label>
                <input
                  type="text"
                  name="location.shelf"
                  className="mt-1 block w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-green-500 focus:border-green-500"
                  value={formData.location.shelf}
                  onChange={handleChange}
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700">Position</label>
                <input
                  type="text"
                  name="location.position"
                  className="mt-1 block w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-green-500 focus:border-green-500"
                  value={formData.location.position}
                  onChange={handleChange}
                />
              </div>
            </div>
          </div>

          <div className="border-t pt-4">
            <h4 className="text-md font-medium text-gray-900 mb-2">Supplier</h4>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700">Supplier Name</label>
                <input
                  type="text"
                  name="supplier.name"
                  className="mt-1 block w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-green-500 focus:border-green-500"
                  value={formData.supplier.name}
                  onChange={handleChange}
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700">Supplier ID</label>
                <input
                  type="text"
                  name="supplier.id"
                  className="mt-1 block w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-green-500 focus:border-green-500"
                  value={formData.supplier.id}
                  onChange={handleChange}
                />
              </div>
            </div>
          </div>

          <div className="flex justify-end space-x-2 pt-4">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 hover:bg-gray-50"
            >
              Cancel
            </button>
            <button
              type="submit"
              className="px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-green-600 hover:bg-green-700"
            >
              {product ? 'Update' : 'Create'} Product
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default ProductModal;

// ==================== CAMERA PAGE ====================
// client/src/pages/Camera.js
import React, { useState, useRef, useCallback } from 'react';
import Webcam from 'react-webcam';
import { Camera as CameraIcon, Upload, RotateCcw, AlertCircle, CheckCircle } from 'lucide-react';
import axios from 'axios';
import { toast } from 'react-toastify';

const Camera = () => {
  const webcamRef = useRef(null);
  const [capturedImage, setCapturedImage] = useState(null);
  const [analyzing, setAnalyzing] = useState(false);
  const [analysisResult, setAnalysisResult] = useState(null);
  const [selectedProduct, setSelectedProduct] = useState('');
  const [products, setProducts] = useState([]);

  React.useEffect(() => {
    fetchProducts();
  }, []);

  const fetchProducts = async () => {
    try {
      const response = await axios.get('/api/products');
      setProducts(response.data);
    } catch (error) {
      console.error('Error fetching products:', error);
    }
  };

  const capture = useCallback(() => {
    const imageSrc = webcamRef.current.getScreenshot();
    setCapturedImage(imageSrc);
  }, [webcamRef]);

  const retake = () => {
    setCapturedImage(null);
    setAnalysisResult(null);
  };

  const analyzeImage = async () => {
    if (!capturedImage) return;

    setAnalyzing(true);
    try {
      // Convert base64 to blob
      const response = await fetch(capturedImage);
      const blob = await response.blob();
      
      const formData = new FormData();
      formData.append('image', blob, 'captured-image.jpg');
      if (selectedProduct) {
        formData.append('productId', selectedProduct);
      }

      const analysisResponse = await axios.post('/api/analyze-image', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });

      setAnalysisResult(analysisResponse.data);
      toast.success('Image analyzed successfully!');
    } catch (error) {
      console.error('Error analyzing image:', error);
      toast.error('Failed to analyze image');
    } finally {
      setAnalyzing(false);
    }
  };

  const handleFileUpload = async (event) => {
    const file = event.target.files[0];
    if (!file) return;

    // Convert file to base64 for preview
    const reader = new FileReader();
    reader.onload = (e) => {
      setCapturedImage(e.target.result);
    };
    reader.readAsDataURL(file);
  };

  const updateProductFreshness = async () => {
    if (!analysisResult || !selectedProduct) return;

    try {
      await axios.put(`/api/products/${selectedProduct}/freshness`, {
        freshnessScore: analysisResult.freshnessScore,
        analysisData: analysisResult
      });
      toast.success('Product freshness updated successfully!');
      setAnalysisResult(null);
      setCapturedImage(null);
      fetchProducts();
    } catch (error) {
      console.error('Error updating product:', error);
      toast.error('Failed to update product freshness');
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold text-gray-900">Freshness Analysis</h1>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Camera/Image Section */}
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">Capture Image</h2>
          
          {!capturedImage ? (
            <div className="space-y-4">
              <div className="relative">
                <Webcam
                  ref={webcamRef}
                  audio={false}
                  height={300}
                  screenshotFormat="image/jpeg"
                  width="100%"
                  videoConstraints={{
                    width: 640,
                    height: 480,
                    facingMode: "user"
                  }}
                  className="rounded-lg"
                />
              </div>
              
              <div className="flex gap-4">
                <button
                  onClick={capture}
                  className="flex-1 inline-flex items-center justify-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-green-600 hover:bg-green-700"
                >
                  <CameraIcon className="h-4 w-4 mr-2" />
                  Capture Photo
                </button>
                
                <div className="flex-1">
                  <label className="w-full inline-flex items-center justify-center px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 cursor-pointer">
                    <Upload className="h-4 w-4 mr-2" />
                    Upload Image
                    <input
                      type="file"
                      accept="image/*"
                      onChange={handleFileUpload}
                      className="hidden"
                    />
                  </label>
                </div>
              </div>
            </div>
          ) : (
            <div className="space-y-4">
              <div className="relative">
                <img
                  src={capturedImage}
                  alt="Captured"
                  className="w-full rounded-lg"
                />
              </div>
              
              <div className="flex gap-4">
                <button
                  onClick={retake}
                  className="flex-1 inline-flex items-center justify-center px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50"
                >
                  <RotateCcw className="h-4 w-4 mr-2" />
                  Retake
                </button>
                
                <button
                  onClick={analyzeImage}
                  disabled={analyzing}
                  className="flex-1 inline-flex items-center justify-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 disabled:opacity-50"
                >
                  {analyzing ? (
                    <>
                      <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                      Analyzing...
                    </>
                  ) : (
                    'Analyze Freshness'
                  )}
                </button>
              </div>
            </div>
          )}
        </div>

        {/* Analysis Results Section */}
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">Analysis Results</h2>
          
          {/* Product Selection */}
          <div className="mb-4">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Select Product (Optional)
            </label>
            <select
              value={selectedProduct}
              onChange={(e) => setSelectedProduct(e.target.value)}
              className="w-full border border-gray-300 rounded-md px-3 py-2 focus:ring-green-500 focus:border-green-500"
            >
              <option value="">Auto-detect product</option>
              {products.map((product) => (
                <option key={product._id} value={product._id}>
                  {product.name} ({product.category})
                </option>
              ))}
            </select>
          </div>

          {!analysisResult && !analyzing && (
            <div className="text-center py-8">
              <CameraIcon className="mx-auto h-12 w-12 text-gray-400" />
              <h3 className="mt-2 text-sm font-medium text-gray-900">No analysis yet</h3>
              <p className="mt-1 text-sm text-gray-500">
                Capture or upload an image to analyze freshness
              </p>
            </div>
          )}

          {analyzing && (
            <div className="text-center py-8">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-green-600 mx-auto"></div>
              <h3 className="mt-2 text-sm font-medium text-gray-900">Analyzing image...</h3>
              <p className="mt-1 text-sm text-gray-500">
                Please wait while we process your image
              </p>
            </div>
          )}

          {analysisResult && (
            <div className="space-y-4">
              {/* Freshness Score */}
              <div className="bg-gray-50 rounded-lg p-4">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm font-medium text-gray-700">Freshness Score</span>
                  <span className={`text-2xl font-bold ${
                    analysisResult.freshnessScore >= 70 ? 'text-green-600' :
                    analysisResult.freshnessScore >= 50 ? 'text-yellow-600' :
                    'text-red-600'
                  }`}>
                    {analysisResult.freshnessScore}%
                  </span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-3">
                  <div
                    className={`h-3 rounded-full ${
                      analysisResult.freshnessScore >= 70 ? 'bg-green-500' :
                      analysisResult.freshnessScore >= 50 ? 'bg-yellow-500' :
                      'bg-red-500'
                    }`}
                    style={{ width: `${analysisResult.freshnessScore}%` }}
                  ></div>
                </div>
              </div>

              {/* Product Info */}
              {analysisResult.detectedProduct && (
                <div className="bg-blue-50 rounded-lg p-4">
                  <h4 className="font-medium text-blue-900 mb-2">Detected Product</h4>
                  <p className="text-blue-800">{analysisResult.detectedProduct}</p>
                  {analysisResult.confidence && (
                    <p className="text-sm text-blue-700 mt-1">
                      Confidence: {(analysisResult.confidence * 100).toFixed(1)}%
                    </p>
                  )}
                </div>
              )}

              {/* Analysis Details */}
              <div className="space-y-3">
                <h4 className="font-medium text-gray-900">Analysis Details</h4>
                
                {analysisResult.factors && analysisResult.factors.map((factor, index) => (
                  <div key={index} className="flex items-start space-x-3">
                    {factor.score >= 70 ? (
                      <CheckCircle className="h-5 w-5 text-green-500 mt-0.5" />
                    ) : (
                      <AlertCircle className="h-5 w-5 text-red-500 mt-0.5" />
                    )}
                    <div className="flex-1">
                      <p className="text-sm font-medium text-gray-900">{factor.name}</p>
                      <p className="text-sm text-gray-600">{factor.description}</p>
                      <div className="mt-1 w-full bg-gray-200 rounded-full h-2">
                        <div
                          className={`h-2 rounded-full ${
                            factor.score >= 70 ? 'bg-green-500' :
                            factor.score >= 50 ? 'bg-yellow-500' :
                            'bg-red-500'
                          }`}
                          style={{ width: `${factor.score}%` }}
                        ></div>
                      </div>
                    </div>
                    <span className="text-sm font-medium text-gray-900">
                      {factor.score}%
                    </span>
                  </div>
                ))}
              </div>

              {/* Recommendations */}
              {analysisResult.recommendations && analysisResult.recommendations.length > 0 && (
                <div className="bg-yellow-50 rounded-lg p-4">
                  <h4 className="font-medium text-yellow-900 mb-2">Recommendations</h4>
                  <ul className="list-disc list-inside space-y-1">
                    {analysisResult.recommendations.map((rec, index) => (
                      <li key={index} className="text-sm text-yellow-800">{rec}</li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Update Product Button */}
              {selectedProduct && (
                <button
                  onClick={updateProductFreshness}
                  className="w-full inline-flex items-center justify-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-green-600 hover:bg-green-700"
                >
                  Update Product Freshness
                </button>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default Camera;


// client/src/pages/Analytics.js
import React, { useState, useEffect } from 'react';
import { 
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
  LineChart, Line, PieChart, Pie, Cell, AreaChart, Area
} from 'recharts';
import { TrendingUp, TrendingDown, DollarSign, AlertTriangle, Package, Calendar } from 'lucide-react';
import axios from 'axios';

const Analytics = () => {
  const [analytics, setAnalytics] = useState(null);
  const [loading, setLoading] = useState(true);
  const [timeRange, setTimeRange] = useState('7days');

  useEffect(() => {
    fetchAnalytics();
  }, [timeRange]);

  const fetchAnalytics = async () => {
    try {
      const response = await axios.get(`/api/analytics?range=${timeRange}`);
      setAnalytics(response.data);
      setLoading(false);
    } catch (error) {
      console.error('Error fetching analytics:', error);
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-green-600"></div>
      </div>
    );
  }

  if (!analytics) {
    return (
      <div className="text-center py-12">
        <AlertTriangle className="mx-auto h-12 w-12 text-gray-400" />
        <h3 className="mt-2 text-sm font-medium text-gray-900">No analytics data available</h3>
      </div>
    );
  }

  const COLORS = ['#10B981', '#F59E0B', '#F97316', '#EF4444'];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold text-gray-900">Analytics</h1>
        <select
          value={timeRange}
          onChange={(e) => setTimeRange(e.target.value)}
          className="border border-gray-300 rounded-md px-3 py-2 focus:ring-green-500 focus:border-green-500"
        >
          <option value="7days">Last 7 Days</option>
          <option value="30days">Last 30 Days</option>
          <option value="90days">Last 90 Days</option>
          <option value="1year">Last Year</option>
        </select>
      </div>

      {/* Key Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <div className="bg-white p-6 rounded-lg shadow">
          <div className="flex items-center">
            <div className="p-2 bg-green-100 rounded-lg">
              <DollarSign className="h-6 w-6 text-green-600" />
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-500">Total Savings</p>
              <p className="text-2xl font-bold text-gray-900">${analytics.totalSavings}</p>
              <p className={`text-sm flex items-center ${
                analytics.savingsChange >= 0 ? 'text-green-600' : 'text-red-600'
              }`}>
                {analytics.savingsChange >= 0 ? (
                  <TrendingUp className="h-4 w-4 mr-1" />
                ) : (
                  <TrendingDown className="h-4 w-4 mr-1" />
                )}
                {Math.abs(analytics.savingsChange)}%
              </p>
            </div>
          </div>
        </div>

        <div className="bg-white p-6 rounded-lg shadow">
          <div className="flex items-center">
            <div className="p-2 bg-blue-100 rounded-lg">
              <Package className="h-6 w-6 text-blue-600" />
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-500">Waste Reduced</p>
              <p className="text-2xl font-bold text-gray-900">{analytics.wasteReduced}kg</p>
              <p className={`text-sm flex items-center ${
                analytics.wasteChange <= 0 ? 'text-green-600' : 'text-red-600'
              }`}>
                {analytics.wasteChange <= 0 ? (
                  <TrendingDown className="h-4 w-4 mr-1" />
                ) : (
                  <TrendingUp className="h-4 w-4 mr-1" />
                )}
                {Math.abs(analytics.wasteChange)}%
              </p>
            </div>
          </div>
        </div>

        <div className="bg-white p-6 rounded-lg shadow">
          <div className="flex items-center">
            <div className="p-2 bg-yellow-100 rounded-lg">
              <TrendingUp className="h-6 w-6 text-yellow-600" />
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-500">Avg Freshness</p>
              <p className="text-2xl font-bold text-gray-900">{analytics.avgFreshness}%</p>
              <p className={`text-sm flex items-center ${
                analytics.freshnessChange >= 0 ? 'text-green-600' : 'text-red-600'
              }`}>
                {analytics.freshnessChange >= 0 ? (
                  <TrendingUp className="h-4 w-4 mr-1" />
                ) : (
                  <TrendingDown className="h-4 w-4 mr-1" />
                )}
                {Math.abs(analytics.freshnessChange)}%
              </p>
            </div>
          </div>
        </div>

        <div className="bg-white p-6 rounded-lg shadow">
          <div className="flex items-center">
            <div className="p-2 bg-red-100 rounded-lg">
              <AlertTriangle className="h-6 w-6 text-red-600" />
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-500">Items at Risk</p>
              <p className="text-2xl font-bold text-gray-900">{analytics.itemsAtRisk}</p>
              <p className={`text-sm flex items-center ${
                analytics.riskChange <= 0 ? 'text-green-600' : 'text-red-600'
              }`}>
                {analytics.riskChange <= 0 ? (
                  <TrendingDown className="h-4 w-4 mr-1" />
                ) : (
                  <TrendingUp className="h-4 w-4 mr-1" />
                )}
                {Math.abs(analytics.riskChange)}%
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Charts Row 1 */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Savings Trend */}
        <div className="bg-white p-6 rounded-lg shadow">
          <h3 className="text-lg font-medium text-gray-900 mb-4">Savings Trend</h3>
          <ResponsiveContainer width="100%" height={300}>
            <AreaChart data={analytics.savingsTrend}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="date" />
              <YAxis />
              <Tooltip formatter={(value) => [`$${value}`, 'Savings']} />
              <Area type="monotone" dataKey="savings" stroke="#10B981" fill="#10B981" fillOpacity={0.6} />
            </AreaChart>
          </ResponsiveContainer>
        </div>

        {/* Waste Reduction */}
        <div className="bg-white p-6 rounded-lg shadow">
          <h3 className="text-lg font-medium text-gray-900 mb-4">Waste Reduction</h3>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={analytics.wasteTrend}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="date" />
              <YAxis />
              <Tooltip formatter={(value) => [`${value}kg`, 'Waste Reduced']} />
              <Line type="monotone" dataKey="waste" stroke="#EF4444" strokeWidth={2} />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Charts Row 2 */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Category Performance */}
        <div className="bg-white p-6 rounded-lg shadow">
          <h3 className="text-lg font-medium text-gray-900 mb-4">Category Performance</h3>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={analytics.categoryPerformance}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="category" />
              <YAxis />
              <Tooltip />
              <Bar dataKey="avgFreshness" fill="#10B981" name="Avg Freshness %" />
              <Bar dataKey="savings" fill="#3B82F6" name="Savings $" />
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Freshness Distribution */}
        <div className="bg-white p-6 rounded-lg shadow">
          <h3 className="text-lg font-medium text-gray-900 mb-4">Current Freshness Distribution</h3>
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={analytics.freshnessDistribution}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                outerRadius={80}
                fill="#8884d8"
                dataKey="value"
              >
                {analytics.freshnessDistribution.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Monthly Summary */}
      <div className="bg-white p-6 rounded-lg shadow">
        <h3 className="text-lg font-medium text-gray-900 mb-4">Monthly Performance Summary</h3>
        <ResponsiveContainer width="100%" height={400}>
          <BarChart data={analytics.monthlyData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="month" />
            <YAxis yAxisId="left" />
            <YAxis yAxisId="right" orientation="right" />
            <Tooltip />
            <Legend />
            <Bar yAxisId="left" dataKey="savings" fill="#10B981" name="Savings ($)" />
            <Bar yAxisId="left" dataKey="wasteReduced" fill="#F59E0B" name="Waste Reduced (kg)" />
            <Line yAxisId="right" type="monotone" dataKey="avgFreshness" stroke="#3B82F6" name="Avg Freshness (%)" />
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* Insights & Recommendations */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Key Insights */}
        <div className="bg-white p-6 rounded-lg shadow">
          <h3 className="text-lg font-medium text-gray-900 mb-4">Key Insights</h3>
          <div className="space-y-3">
            {analytics.insights.map((insight, index) => (
              <div key={index} className="flex items-start space-x-3">
                <div className={`p-1 rounded-full ${
                  insight.type === 'positive' ? 'bg-green-100' :
                  insight.type === 'negative' ? 'bg-red-100' : 'bg-yellow-100'
                }`}>
                  {insight.type === 'positive' ? (
                    <TrendingUp className="h-4 w-4 text-green-600" />
                  ) : insight.type === 'negative' ? (
                    <TrendingDown className="h-4 w-4 text-red-600" />
                  ) : (
                    <AlertTriangle className="h-4 w-4 text-yellow-600" />
                  )}
                </div>
                <p className="text-sm text-gray-700">{insight.text}</p>
              </div>
            ))}
          </div>
        </div>

        {/* Recommendations */}
        <div className="bg-white p-6 rounded-lg shadow">
          <h3 className="text-lg font-medium text-gray-900 mb-4">Recommendations</h3>
          <div className="space-y-3">
            {analytics.recommendations.map((rec, index) => (
              <div key={index} className="p-3 bg-blue-50 rounded-lg">
                <p className="text-sm font-medium text-blue-900">{rec.title}</p>
                <p className="text-sm text-blue-800 mt-1">{rec.description}</p>
                {rec.impact && (
                  <p className="text-xs text-blue-700 mt-2">
                    Potential impact: {rec.impact}
                  </p>
                )}
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

export default Analytics;


// client/src/pages/Settings.js
import React, { useState, useEffect } from 'react';
import { Save, Bell, Shield, Database, Palette, Globe, AlertCircle, CheckCircle } from 'lucide-react';
import axios from 'axios';
import { toast } from 'react-toastify';

const Settings = () => {
  const [settings, setSettings] = useState({
    notifications: {
      emailAlerts: true,
      pushNotifications: true,
      freshnessThreshold: 70,
      expiryWarningDays: 3,
      dailyReports: false,
      weeklyReports: true
    },
    pricing: {
      dynamicPricing: true,
      maxDiscountPercent: 50,
      minDiscountPercent: 10,
      pricingStrategy: 'linear'
    },
    analysis: {
      autoAnalysis: true,
      analysisFrequency: 'daily',
      confidenceThreshold: 0.8,
      enableMachineLearning: true
    },
    general: {
      currency: 'USD',
      timezone: 'America/New_York',
      language: 'en',
      theme: 'light',
      companyName: 'FreshGuard Solutions',
      contactEmail: 'admin@freshguard.com'
    }
  });

  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [activeTab, setActiveTab] = useState('notifications');
  const [hasChanges, setHasChanges] = useState(false);

  useEffect(() => {
    fetchSettings();
  }, []);

  const fetchSettings = async () => {
    try {
      const response = await axios.get('/api/settings');
      setSettings(response.data);
      setLoading(false);
    } catch (error) {
      console.error('Error fetching settings:', error);
      toast.error('Failed to load settings');
      setLoading(false);
    }
  };

  const handleSettingChange = (category, key, value) => {
    setSettings(prev => ({
      ...prev,
      [category]: {
        ...prev[category],
        [key]: value
      }
    }));
    setHasChanges(true);
  };

  const validateSettings = () => {
    const errors = [];

    // Validate notifications
    if (settings.notifications.freshnessThreshold < 0 || settings.notifications.freshnessThreshold > 100) {
      errors.push('Freshness threshold must be between 0 and 100');
    }
    if (settings.notifications.expiryWarningDays < 1 || settings.notifications.expiryWarningDays > 30) {
      errors.push('Expiry warning days must be between 1 and 30');
    }

    // Validate pricing
    if (settings.pricing.maxDiscountPercent <= settings.pricing.minDiscountPercent) {
      errors.push('Maximum discount must be greater than minimum discount');
    }
    if (settings.pricing.minDiscountPercent < 0 || settings.pricing.maxDiscountPercent > 100) {
      errors.push('Discount percentages must be between 0 and 100');
    }

    // Validate analysis
    if (settings.analysis.confidenceThreshold < 0 || settings.analysis.confidenceThreshold > 1) {
      errors.push('Confidence threshold must be between 0 and 1');
    }

    // Validate general
    if (!settings.general.companyName.trim()) {
      errors.push('Company name is required');
    }
    if (!settings.general.contactEmail.trim() || !isValidEmail(settings.general.contactEmail)) {
      errors.push('Valid contact email is required');
    }

    return errors;
  };

  const isValidEmail = (email) => {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
  };

  const saveSettings = async () => {
    const validationErrors = validateSettings();
    if (validationErrors.length > 0) {
      validationErrors.forEach(error => toast.error(error));
      return;
    }

    setSaving(true);
    try {
      await axios.put('/api/settings', settings);
      toast.success('Settings saved successfully');
      setHasChanges(false);
    } catch (error) {
      console.error('Error saving settings:', error);
      toast.error('Failed to save settings');
    } finally {
      setSaving(false);
    }
  };

  const resetToDefaults = () => {
    if (window.confirm('Are you sure you want to reset all settings to default values?')) {
      setSettings({
        notifications: {
          emailAlerts: true,
          pushNotifications: true,
          freshnessThreshold: 70,
          expiryWarningDays: 3,
          dailyReports: false,
          weeklyReports: true
        },
        pricing: {
          dynamicPricing: true,
          maxDiscountPercent: 50,
          minDiscountPercent: 10,
          pricingStrategy: 'linear'
        },
        analysis: {
          autoAnalysis: true,
          analysisFrequency: 'daily',
          confidenceThreshold: 0.8,
          enableMachineLearning: true
        },
        general: {
          currency: 'USD',
          timezone: 'America/New_York',
          language: 'en',
          theme: 'light',
          companyName: 'FreshGuard Solutions',
          contactEmail: 'admin@freshguard.com'
        }
      });
      setHasChanges(true);
    }
  };

  const tabs = [
    { id: 'notifications', label: 'Notifications', icon: Bell },
    { id: 'pricing', label: 'Pricing', icon: Database },
    { id: 'analysis', label: 'Analysis', icon: Shield },
    { id: 'general', label: 'General', icon: Globe }
  ];

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-blue-500"></div>
      </div>
    );
  }

  return (
    <div className="max-w-6xl mx-auto p-6">
      <div className="bg-white rounded-lg shadow-lg">
        {/* Header */}
        <div className="border-b border-gray-200 px-6 py-4">
          <div className="flex justify-between items-center">
            <h1 className="text-2xl font-bold text-gray-900">Settings</h1>
            <div className="flex gap-3">
              <button
                onClick={resetToDefaults}
                className="px-4 py-2 text-gray-600 hover:text-gray-800 transition-colors"
              >
                Reset to Defaults
              </button>
              <button
                onClick={saveSettings}
                disabled={!hasChanges || saving}
                className={`flex items-center gap-2 px-4 py-2 rounded-lg transition-colors ${
                  hasChanges && !saving
                    ? 'bg-blue-600 text-white hover:bg-blue-700'
                    : 'bg-gray-300 text-gray-500 cursor-not-allowed'
                }`}
              >
                <Save className="w-4 h-4" />
                {saving ? 'Saving...' : 'Save Changes'}
              </button>
            </div>
          </div>
          {hasChanges && (
            <div className="mt-2 flex items-center gap-2 text-amber-600">
              <AlertCircle className="w-4 h-4" />
              <span className="text-sm">You have unsaved changes</span>
            </div>
          )}
        </div>

        <div className="flex">
          {/* Sidebar */}
          <div className="w-64 border-r border-gray-200">
            <nav className="p-4">
              {tabs.map((tab) => {
                const Icon = tab.icon;
                return (
                  <button
                    key={tab.id}
                    onClick={() => setActiveTab(tab.id)}
                    className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg text-left transition-colors ${
                      activeTab === tab.id
                        ? 'bg-blue-50 text-blue-700 border-r-2 border-blue-600'
                        : 'text-gray-600 hover:bg-gray-50'
                    }`}
                  >
                    <Icon className="w-5 h-5" />
                    {tab.label}
                  </button>
                );
              })}
            </nav>
          </div>

          {/* Content */}
          <div className="flex-1 p-6">
            {activeTab === 'notifications' && (
              <div className="space-y-6">
                <h2 className="text-xl font-semibold text-gray-900">Notification Settings</h2>
                
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div className="space-y-4">
                    <h3 className="font-medium text-gray-900">Alert Preferences</h3>
                    
                    <label className="flex items-center gap-3">
                      <input
                        type="checkbox"
                        checked={settings.notifications.emailAlerts}
                        onChange={(e) => handleSettingChange('notifications', 'emailAlerts', e.target.checked)}
                        className="w-4 h-4 text-blue-600 rounded focus:ring-blue-500"
                      />
                      <span>Email Alerts</span>
                    </label>

                    <label className="flex items-center gap-3">
                      <input
                        type="checkbox"
                        checked={settings.notifications.pushNotifications}
                        onChange={(e) => handleSettingChange('notifications', 'pushNotifications', e.target.checked)}
                        className="w-4 h-4 text-blue-600 rounded focus:ring-blue-500"
                      />
                      <span>Push Notifications</span>
                    </label>

                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        Freshness Threshold (%)
                      </label>
                      <input
                        type="number"
                        min="0"
                        max="100"
                        value={settings.notifications.freshnessThreshold}
                        onChange={(e) => handleSettingChange('notifications', 'freshnessThreshold', parseInt(e.target.value))}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                      />
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        Expiry Warning (days)
                      </label>
                      <input
                        type="number"
                        min="1"
                        max="30"
                        value={settings.notifications.expiryWarningDays}
                        onChange={(e) => handleSettingChange('notifications', 'expiryWarningDays', parseInt(e.target.value))}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                      />
                    </div>
                  </div>

                  <div className="space-y-4">
                    <h3 className="font-medium text-gray-900">Report Settings</h3>
                    
                    <label className="flex items-center gap-3">
                      <input
                        type="checkbox"
                        checked={settings.notifications.dailyReports}
                        onChange={(e) => handleSettingChange('notifications', 'dailyReports', e.target.checked)}
                        className="w-4 h-4 text-blue-600 rounded focus:ring-blue-500"
                      />
                      <span>Daily Reports</span>
                    </label>

                    <label className="flex items-center gap-3">
                      <input
                        type="checkbox"
                        checked={settings.notifications.weeklyReports}
                        onChange={(e) => handleSettingChange('notifications', 'weeklyReports', e.target.checked)}
                        className="w-4 h-4 text-blue-600 rounded focus:ring-blue-500"
                      />
                      <span>Weekly Reports</span>
                    </label>
                  </div>
                </div>
              </div>
            )}

            {activeTab === 'pricing' && (
              <div className="space-y-6">
                <h2 className="text-xl font-semibold text-gray-900">Pricing Settings</h2>
                
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div className="space-y-4">
                    <h3 className="font-medium text-gray-900">Dynamic Pricing</h3>
                    
                    <label className="flex items-center gap-3">
                      <input
                        type="checkbox"
                        checked={settings.pricing.dynamicPricing}
                        onChange={(e) => handleSettingChange('pricing', 'dynamicPricing', e.target.checked)}
                        className="w-4 h-4 text-blue-600 rounded focus:ring-blue-500"
                      />
                      <span>Enable Dynamic Pricing</span>
                    </label>

                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        Pricing Strategy
                      </label>
                      <select
                        value={settings.pricing.pricingStrategy}
                        onChange={(e) => handleSettingChange('pricing', 'pricingStrategy', e.target.value)}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                      >
                        <option value="linear">Linear</option>
                        <option value="exponential">Exponential</option>
                        <option value="threshold">Threshold-based</option>
                      </select>
                    </div>
                  </div>

                  <div className="space-y-4">
                    <h3 className="font-medium text-gray-900">Discount Limits</h3>
                    
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        Maximum Discount (%)
                      </label>
                      <input
                        type="number"
                        min="0"
                        max="100"
                        value={settings.pricing.maxDiscountPercent}
                        onChange={(e) => handleSettingChange('pricing', 'maxDiscountPercent', parseInt(e.target.value))}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                      />
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        Minimum Discount (%)
                      </label>
                      <input
                        type="number"
                        min="0"
                        max="100"
                        value={settings.pricing.minDiscountPercent}
                        onChange={(e) => handleSettingChange('pricing', 'minDiscountPercent', parseInt(e.target.value))}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                      />
                    </div>
                  </div>
                </div>
              </div>
            )}

            {activeTab === 'analysis' && (
              <div className="space-y-6">
                <h2 className="text-xl font-semibold text-gray-900">Analysis Settings</h2>
                
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div className="space-y-4">
                    <h3 className="font-medium text-gray-900">Automation</h3>
                    
                    <label className="flex items-center gap-3">
                      <input
                        type="checkbox"
                        checked={settings.analysis.autoAnalysis}
                        onChange={(e) => handleSettingChange('analysis', 'autoAnalysis', e.target.checked)}
                        className="w-4 h-4 text-blue-600 rounded focus:ring-blue-500"
                      />
                      <span>Auto Analysis</span>
                    </label>

                    <label className="flex items-center gap-3">
                      <input
                        type="checkbox"
                        checked={settings.analysis.enableMachineLearning}
                        onChange={(e) => handleSettingChange('analysis', 'enableMachineLearning', e.target.checked)}
                        className="w-4 h-4 text-blue-600 rounded focus:ring-blue-500"
                      />
                      <span>Enable Machine Learning</span>
                    </label>

                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        Analysis Frequency
                      </label>
                      <select
                        value={settings.analysis.analysisFrequency}
                        onChange={(e) => handleSettingChange('analysis', 'analysisFrequency', e.target.value)}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                      >
                        <option value="hourly">Hourly</option>
                        <option value="daily">Daily</option>
                        <option value="weekly">Weekly</option>
                      </select>
                    </div>
                  </div>

                  <div className="space-y-4">
                    <h3 className="font-medium text-gray-900">Thresholds</h3>
                    
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        Confidence Threshold
                      </label>
                      <input
                        type="number"
                        min="0"
                        max="1"
                        step="0.01"
                        value={settings.analysis.confidenceThreshold}
                        onChange={(e) => handleSettingChange('analysis', 'confidenceThreshold', parseFloat(e.target.value))}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                      />
                      <p className="text-sm text-gray-500 mt-1">Value between 0 and 1</p>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {activeTab === 'general' && (
              <div className="space-y-6">
                <h2 className="text-xl font-semibold text-gray-900">General Settings</h2>
                
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div className="space-y-4">
                    <h3 className="font-medium text-gray-900">Company Information</h3>
                    
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        Company Name
                      </label>
                      <input
                        type="text"
                        value={settings.general.companyName}
                        onChange={(e) => handleSettingChange('general', 'companyName', e.target.value)}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                      />
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        Contact Email
                      </label>
                      <input
                        type="email"
                        value={settings.general.contactEmail}
                        onChange={(e) => handleSettingChange('general', 'contactEmail', e.target.value)}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                      />
                    </div>
                  </div>

                  <div className="space-y-4">
                    <h3 className="font-medium text-gray-900">Localization</h3>
                    
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        Currency
                      </label>
                      <select
                        value={settings.general.currency}
                        onChange={(e) => handleSettingChange('general', 'currency', e.target.value)}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                      >
                        <option value="USD">USD - US Dollar</option>
                        <option value="EUR">EUR - Euro</option>
                        <option value="GBP">GBP - British Pound</option>
                        <option value="CAD">CAD - Canadian Dollar</option>
                        <option value="INR">INR - Indian Rupee</option>
                      </select>
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        Timezone
                      </label>
                      <select
                        value={settings.general.timezone}
                        onChange={(e) => handleSettingChange('general', 'timezone', e.target.value)}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                      >
                        <option value="America/New_York">Eastern Time</option>
                        <option value="America/Chicago">Central Time</option>
                        <option value="America/Denver">Mountain Time</option>
                        <option value="America/Los_Angeles">Pacific Time</option>
                        <option value="Europe/London">London</option>
                        <option value="Europe/Paris">Paris</option>
                        <option value="Asia/Tokyo">Tokyo</option>
                        <option value="Asia/Kolkata">Kolkata</option>
                      </select>
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        Language
                      </label>
                      <select
                        value={settings.general.language}
                        onChange={(e) => handleSettingChange('general', 'language', e.target.value)}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                      >
                        <option value="en">English</option>
                        <option value="es">Spanish</option>
                        <option value="fr">French</option>
                        <option value="de">German</option>
                        <option value="hi">Hindi</option>
                      </select>
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        Theme
                      </label>
                      <select
                        value={settings.general.theme}
                        onChange={(e) => handleSettingChange('general', 'theme', e.target.value)}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                      >
                        <option value="light">Light</option>
                        <option value="dark">Dark</option>
                        <option value="auto">Auto</option>
                      </select>
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default Settings;
