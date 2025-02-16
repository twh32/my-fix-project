import React, { useEffect, useState } from 'react';
import axios from 'axios';

function InternalSystemUI() {
  const [orders, setOrders] = useState([]);

  const fetchOrders = async () => {
    try {
      const response = await axios.get('http://localhost:5002/orders');
      setOrders(response.data.orders);
    } catch (error) {
      console.error('Error fetching orders:', error);
    }
  };

  useEffect(() => {
    fetchOrders();
    // Poll for new orders every 10 seconds.
    const interval = setInterval(fetchOrders, 10000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div>
      <h2>Internal System - Order Viewer</h2>
      <table border="1" cellPadding="5">
        <thead>
          <tr>
            <th>Order ID</th>
            <th>Symbol</th>
            <th>Quantity</th>
            <th>Price</th>
            <th>Ingested Timestamp</th>
          </tr>
        </thead>
        <tbody>
          {orders.length > 0 ? (
            orders.map((order, idx) => (
              <tr key={idx}>
                <td>{order.order_id}</td>
                <td>{order.symbol}</td>
                <td>{order.quantity}</td>
                <td>{order.price}</td>
                <td>{order.ingested_timestamp}</td>
              </tr>
            ))
          ) : (
            <tr>
              <td colSpan="5">No orders available.</td>
            </tr>
          )}
        </tbody>
      </table>
    </div>
  );
}

export default InternalSystemUI;