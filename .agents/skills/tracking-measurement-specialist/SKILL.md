---
name: tracking-measurement-specialist
description: 追蹤與成效衡量專家 - 專精於驗證轉換追蹤準確性、代碼部署及數據一致性檢查。
---

# 追蹤與成效衡量專家 (Tracking & Measurement Specialist)

本技能指導如何對新接管的網站進行代碼部署與數據追蹤精準度的驗證，確保所有廣告轉換數據皆能被正確收集與回傳。

## 1. 基礎追蹤代碼稽核 (Baseline Tags Audit)
- **Tag 部署確認**：檢查 Google Tag (gtag.js)、Google Tag Manager (GTM) 容器程式碼是否已正確安裝在網頁的 `<head>` 與 `<body>` 中。
- **第三方代碼驗證**：確認 Meta Pixel、TikTok Pixel 或 LINE Tag 是否已部署，且在頁面載入時正確觸發 `PageView` 事件。
- **Consent Mode 狀態**：在適用地區（如歐洲或隱私規範嚴格的區域）驗證 Google Consent Mode v2 是否已正確設定，以符合合規要求。

## 2. 轉換追蹤與事件驗證 (Conversion Tracking Validation)
- **關鍵事件檢查**：驗證購買 (Purchase)、加入購物車 (AddToCart)、預訂確認等核心事件是否重複觸發 (Double Counting) 或漏失。
- **增強型轉換 (Enhanced Conversions)**：確認是否已啟用並正確回傳加密的用戶自訂資料（如 Email、電話），以提高廣告歸因的精準度。
- **資料層 (DataLayer) 審查**：檢查電子商務事件（如 GA4 e-commerce events）的 `items` 陣列結構、`value` 和 `currency` 是否正確傳遞給 GTM。

## 3. 跨網域與平台對齊 (GA4 & Ad Platforms Alignment)
- **GA4 設定**：確保已排除參照網址（如第三方金流 LINE Pay、Stripe 的網址），避免轉換被錯誤歸因給金流平台。
- **後端與前端比對**：比對後端資料庫真實預訂量與 Google Ads / GA4 中的紀錄，確認落差比例（正常應在 5% - 10% 內）。

## 4. 寫作細節與自我審查清單
- [ ] 是否完全使用**繁體中文（台灣，zh-TW）**？
- [ ] 是否在**中英文與數字之間加上了半形空格**？
