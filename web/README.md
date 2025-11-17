# Web GUI for ML House Price Predictor

A beautiful, user-friendly web interface for making house price predictions using the ML API.

## Features

- 🎨 **Beautiful UI**: Modern, responsive design with gradient background
- 📊 **Real-time Predictions**: Instant predictions from your ML model
- 📈 **Confidence Intervals**: Optional 95% confidence interval display
- 🔄 **Quick Presets**: Pre-filled examples for testing (Luxury SF, Average LA, Budget Valley)
- ✅ **Health Check**: Test API connection before making predictions
- 📱 **Responsive**: Works on desktop, tablet, and mobile
- 🎯 **User-Friendly**: Clear labels, tooltips, and validation

## Quick Start

### Option 1: Python Web Server (Recommended)

```bash
# From project root
python web/serve.py

# Or specify a different port
python web/serve.py 8000
```

Then open http://localhost:8080 in your browser.

### Option 2: Direct File Access

Simply open `web/index.html` directly in your browser:

```bash
open web/index.html  # macOS
```

Note: Direct file access may have CORS restrictions. Use the Python server for best results.

### Option 3: Using Make

```bash
# From project root
make web
```

## Usage

1. **Start LocalStack and Deploy API**
   ```bash
   make start-localstack
   make deploy-all
   ```

2. **Get your API Gateway URL**
   ```bash
   make api-url
   ```

3. **Start the Web Server**
   ```bash
   make web
   ```

4. **Open Browser**
   - Navigate to http://localhost:8080
   - Enter your API Gateway URL in the configuration section
   - Click "Test Connection" to verify connectivity

5. **Make Predictions**
   - Use quick presets or enter custom values
   - Click "Predict Price" for a simple prediction
   - Click "Predict with Confidence Interval" for detailed results

## API Configuration

The web interface needs your API Gateway URL. You can find it using:

```bash
# Get API URL
aws --endpoint-url=http://localhost:4566 apigateway get-rest-apis

# The URL format is:
http://localhost:4566/restapis/{api-id}/prod/_user_request_
```

Or simply use:
```bash
make api-url
```

## Features Explained

### Quick Presets

- **💎 Luxury SF**: High-income San Francisco property
  - Median Income: $83,252
  - 41 years old
  - San Francisco coordinates

- **🏡 Average LA**: Typical Los Angeles property
  - Median Income: $38,000
  - 25 years old
  - Los Angeles coordinates

- **💰 Budget Valley**: Affordable Central Valley property
  - Median Income: $25,000
  - 15 years old
  - Central Valley coordinates

### Input Fields

All 8 California Housing features:

1. **Median Income**: Household income in $10,000s (e.g., 8.3 = $83,000)
2. **House Age**: Median age of houses in the block
3. **Avg Rooms**: Average number of rooms per household
4. **Avg Bedrooms**: Average number of bedrooms per household
5. **Population**: Block group population
6. **Avg Occupancy**: Average household members
7. **Latitude**: Geographic latitude
8. **Longitude**: Geographic longitude

### Prediction Results

The interface displays:
- **Predicted Price**: Main prediction in USD
- **Confidence Interval** (when requested): 95% confidence range
- **Standard Deviation**: Model uncertainty
- **Input Features**: Summary of submitted values

## Troubleshooting

### "Connection Failed" Error

**Cause**: Cannot connect to API Gateway

**Solutions**:
1. Check LocalStack is running: `docker ps | grep localstack`
2. Verify API is deployed: `make api-url`
3. Test API manually: `make health`
4. Check URL format (should end with `_user_request_`)

### CORS Errors (in browser console)

**Cause**: Browser blocking cross-origin requests

**Solutions**:
1. Use the Python web server instead of direct file access
2. Make sure you're accessing via `http://localhost:8080`, not `file://`

### "Model not loaded" Error

**Cause**: Lambda cannot find model in S3

**Solutions**:
1. Train and upload model: `make train`
2. Check S3 bucket: `make s3-models`
3. Redeploy Lambda: `cd infrastructure && npm run deploy:local`

### Prediction Takes Too Long

**Cause**: Lambda cold start (first request)

**What's happening**: Lambda is loading scikit-learn and downloading model from S3

**Solutions**:
- Wait 5-10 seconds for first request
- Subsequent requests will be much faster (~100-300ms)
- This is normal for serverless functions

## Customization

### Change Port

```python
python web/serve.py 3000  # Run on port 3000
```

### Modify Presets

Edit `web/index.html` and update the `presets` object:

```javascript
const presets = {
    luxury: { medInc: 8.3252, houseAge: 41, ... },
    average: { medInc: 3.8, houseAge: 25, ... },
    budget: { medInc: 2.5, houseAge: 15, ... }
};
```

### Styling

All CSS is embedded in `web/index.html`. Modify the `<style>` section to customize:
- Colors
- Fonts
- Layout
- Animations

## Integration with Real AWS

When deploying to real AWS:

1. Deploy infrastructure: `cd infrastructure && npm run deploy`
2. Get API URL from CloudFormation outputs
3. Update the web interface with the new URL
4. Optionally deploy the web interface to S3 + CloudFront

## Security Notes

**For Production**:
- Don't expose LocalStack endpoints publicly
- Use HTTPS for API Gateway
- Implement API authentication (API Keys, Cognito, etc.)
- Add rate limiting
- Validate all inputs on the backend

## Browser Support

Tested on:
- ✅ Chrome/Edge (latest)
- ✅ Firefox (latest)
- ✅ Safari (latest)
- ✅ Mobile browsers

## File Structure

```
web/
├── index.html      # Main web interface (HTML + CSS + JS)
├── serve.py        # Python web server with CORS
└── README.md       # This file
```

## Technologies Used

- **HTML5**: Structure
- **CSS3**: Styling (no frameworks!)
- **Vanilla JavaScript**: Functionality (no dependencies!)
- **Python**: Simple HTTP server

No build process, no dependencies, just open and use! 🚀
