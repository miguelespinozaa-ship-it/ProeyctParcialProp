import { Navigate, Route, Routes } from "react-router-dom";
import ProtectedRoute from "./auth/ProtectedRoute";
import Login from "./pages/Login";
import Register from "./pages/Register";
import CustomerHome from "./pages/customer/CustomerHome";
import RestaurantMenu from "./pages/customer/RestaurantMenu";
import OrderTracking from "./pages/customer/OrderTracking";
import AdminDashboard from "./pages/admin/AdminDashboard";
import AdminMenu from "./pages/admin/AdminMenu";
import AdminAnalytics from "./pages/admin/AdminAnalytics";
import DeliveryDashboard from "./pages/delivery/DeliveryDashboard";

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Navigate to="/login" replace />} />
      <Route path="/login" element={<Login />} />
      <Route path="/register" element={<Register />} />

      <Route
        path="/customer"
        element={
          <ProtectedRoute rol="customer">
            <CustomerHome />
          </ProtectedRoute>
        }
      />
      <Route
        path="/customer/restaurants/:id"
        element={
          <ProtectedRoute rol="customer">
            <RestaurantMenu />
          </ProtectedRoute>
        }
      />
      <Route
        path="/customer/orders/:id"
        element={
          <ProtectedRoute rol="customer">
            <OrderTracking />
          </ProtectedRoute>
        }
      />

      <Route
        path="/admin"
        element={
          <ProtectedRoute rol="admin">
            <AdminDashboard />
          </ProtectedRoute>
        }
      />
      <Route
        path="/admin/menu"
        element={
          <ProtectedRoute rol="admin">
            <AdminMenu />
          </ProtectedRoute>
        }
      />
      <Route
        path="/admin/analytics"
        element={
          <ProtectedRoute rol="admin">
            <AdminAnalytics />
          </ProtectedRoute>
        }
      />

      <Route
        path="/delivery"
        element={
          <ProtectedRoute rol="delivery">
            <DeliveryDashboard />
          </ProtectedRoute>
        }
      />

      <Route path="*" element={<Navigate to="/login" replace />} />
    </Routes>
  );
}
