import React, { useState } from 'react';
import axios from 'axios';

function ClientOrderUI() {
  const [orderId, setOrderId] = useState('');
  const [symbol, setSymbol] = useState('');
  const [quantity, setQuantity] = useState('');
  const [price, setPrice] = useState('');
  const [message, setMessage] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();

    const order = {
      order_id: orderId,
      symbol,
      quantity: parseInt(quantity, 10),
      price: parseFloat(price),
      business_unit: 'BU-001',
      trader_id: 'TRADER001',
      risk_category: 'LOW',
      processed_timestamp: new Date().toISOString(),
    };

    try {
      // Use a relative path so it calls the same origin (Heroku or local dev).
      const response = await axios.post('/orders', order);
      setMessage(`Success: ${response.data.message}`);
    } catch (error) {
      setMessage(`Error: ${
        error.response ? error.response.data.message : error.message
      }`);
    }
  };

  return (
    <div>
      <h2>Client Order UI</h2>
      <form onSubmit={handleSubmit}>
        <div>
          <label>Order ID:</label>
          <input
            type="text"
            value={orderId}
            onChange={(e) => setOrderId(e.target.value)}
            required
          />
        </div>
        <div>
          <label>Symbol:</label>
          <input
            type="text"
            value={symbol}
            onChange={(e) => setSymbol(e.target.value)}
            required
          />
        </div>
        <div>
          <label>Quantity:</label>
          <input
            type="number"
            value={quantity}
            onChange={(e) => setQuantity(e.target.value)}
            required
          />
        </div>
        <div>
          <label>Price:</label>
          <input
            type="number"
            step="0.01"
            value={price}
            onChange={(e) => setPrice(e.target.value)}
            required
          />
        </div>
        <button type="submit">Submit Order</button>
      </form>
      {message && <p>{message}</p>}
    </div>
  );
}

export default ClientOrderUI;