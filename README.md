
# IBKR Custom Config

This repository provides a custom configuration system for automating trading strategies with Interactive Brokers (IBKR). It is designed to integrate with external signal sources (e.g., TradingView) and allow remote configuration via Telegram.

---

## 📊 Architecture Diagram

```
+------------------+       +-------------------+       +----------------------+
|  TradingView     | ----> |  Webhook Listener | ----> |  Trade Decision Logic |
+------------------+       +-------------------+       +----------------------+
                                                           |
                                                           v
+------------------+       +-------------------+       +----------------------+
|  Telegram Bot    | <---- |  Config Manager   | ----> |     IBKR API         |
+------------------+       +-------------------+       +----------------------+
```

---

## ✅ Features

- 📈 Signal-based trading with TradingView webhooks  
- 💬 Live configuration via Telegram bot commands  
- 🔒 Secure integration with Interactive Brokers API  
- ⚙️ Modular design for easy customization  
- 💹 Support for DCA, take-profit, and future expansion  

---

## 🚀 Getting Started

1. **Clone the Repository**
   ```bash
   git clone https://github.com/KamranAliOfficial/ibkr-custom-config.git
   cd ibkr-custom-config
   ```

2. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set Up Configuration**
   - Add your Telegram Bot Token & Chat ID  
   - Provide IBKR gateway details (TWS or IB Gateway)  
   - Configure environment variables or `.env` file  

4. **Run the Bot**
   ```bash
   python bot.py
   ```

---

## 🛠️ TODO

- [ ] Add automated testing  
- [ ] Expand error handling/logging  
- [ ] Build profit-taking and DCA modules  
- [ ] Add Docker support for easy deployment  

---

## 📄 License

MIT License

---

### Made with ❤️ by **Kamran Ali**
