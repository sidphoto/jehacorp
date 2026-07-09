# 📡 追蹤與成效衡量驗證報告 — Test
已完成「Test」的網站代碼與轉換追蹤驗證。

## 1. 追蹤設定檢查結果
- Google Tag Manager (GTM): 已正確部署於 `<head>`。
- Meta Pixel: 正常觸發 `PageView`，但 `InitiateCheckout` 事件缺少參數 `value` 與 `currency`。
- Google Analytics 4 (GA4): 發現金流跳轉（例如 LINE Pay / MoMo）未加入「排除參照網址」，導致部分轉換被錯誤歸因。

## 2. 建議修正清單
- [ ] 將第三方金流網址加入 GA4 的排除名單。
- [ ] 補齊 Meta Pixel 的電子商務事件參數。
