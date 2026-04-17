# 🚀 Universal Widget Integration Guide

Your AI Chat Widget is now a **High-Performance Single-Script Plugin**. You can embed the entire experience—styles and logic—with just one line of code.

## 1. Production Build
Ensure you are using your live backend URL, then build the widget:
```powershell
cd frontend/widget
npm.cmd run build
```

## 2. Hosting the Assets
Upload the contents of the `widget/frontend/dist` folder to your CDN or web host.
- **Your Script URL**: `https://your-host.com/assets/widget.js`

## 3. The "Single-Script" Integration
Paste this snippet into any website’s `index.html`. 

```html
<!-- 1. The Single Source (No CSS link required!) -->
<script type="module" src="https://your-host.com/assets/widget.js"></script>

<!-- 2. Initialize Branding -->
<script>
    document.addEventListener('DOMContentLoaded', () => {
        window.ChatWidget.init({
            botName: "F.R.I.D.A.Y",
            apiUrl: "https://your-api.com/chat"
        });
    });
</script>
```

### Advanced Options
| Parameter | Description |
|-----------|-------------|
| `botName` | Customizes the header title. |
| `welcomeMessage` | Sets the first message users see. |
| `apiUrl` | Routes requests to your AI server. |
| `id` | Custom mount container ID (optional). |

## 4. Backend CORS (Safety First)
As always, authorize the new domain in your backend `.env`:
```env
ALLOWED_ORIGINS=https://your-new-website.com
```

---
> [!NOTE]
> **No CSS Required**
> Thanks to our new injection engine, the styles are automatically loaded the moment the script runs. This prevents FOUC (Flash of Unstyled Content) and makes your integration code much cleaner.
