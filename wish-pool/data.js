/**
 * Wish Pool - 模擬資料庫與 LocalStorage 控制層
 * 設計者：Backend & DB Engineer
 */

const STORAGE_KEY = 'wish_pool_data';

// 台灣在地特色初始提案數據
const DEFAULT_WISHES = [
  {
    id: "wish_1719912300001",
    title: "推動『開源 AI 繁體中文本土模型』維護計畫",
    description: "目前的 LLM 模型在繁體中文（台灣）的特殊用語、歷史文化及法律背景上仍常有落差。希望能建立一個開源社群與基金，專門維護並微調適合台灣用字與文化習慣的繁體中文大語言模型，並開放大眾免費商業使用。",
    expectedEffect: "讓台灣的中小企業、學生、獨立開發者有高品質且無版權疑慮的本土 AI 模型可以使用，提升台灣整體數位競爭力。",
    category: "科技創新",
    creator: "開源阿豪",
    status: "Voting", // Proposed (提案中), Voting (附議中), Reviewing (評估中), Accepted (已採納), Implemented (已實現), Declined (暫不考慮)
    createdAt: "2026-07-05T08:30:00.000Z",
    votes: 82,
    targetVotes: 100,
    voters: ["voter_init_1", "voter_init_2"], // 模擬已投票的使用者
    officialResponse: "",
    comments: [
      {
        id: "comment_1",
        author: "小林",
        content: "非常支持！很多國外模型翻譯腔很重，且常把台灣地名或制度搞錯，真的需要本土資料集微調。",
        createdAt: "2026-07-05T09:12:00.000Z",
        isAdmin: false
      },
      {
        id: "comment_2",
        author: "AI 研究生",
        content: "如果能釋出 GGUF 格式，讓本機運行更順暢就太棒了！願意一起貢獻算力與語料。",
        createdAt: "2026-07-05T10:05:00.000Z",
        isAdmin: false
      }
    ]
  },
  {
    id: "wish_1719912300002",
    title: "建置『大眾運輸工具之寵物友善車廂』",
    description: "許多毛爸媽因為攜帶中大型寵物（如黃金獵犬、邊境牧羊犬）無法搭乘大眾運輸，只能花費高昂計程車費。希望能推動捷運與公車在離峰時段設立專屬的『寵物友善車廂』，在遵守繫繩與戴口罩（視情況）的前提下，免裝箱直接搭乘。",
    expectedEffect: "減少毛家庭的交通負擔，同時宣導寵物社會化，建立多元友善的溫馨都市環境。",
    category: "生活便利",
    creator: "邊境多比媽",
    status: "Reviewing",
    createdAt: "2026-07-04T12:00:00.000Z",
    votes: 124,
    targetVotes: 100,
    voters: [],
    officialResponse: "【交通局官方回應】：感謝提案。本局目前已於部分特定公車路線試辦寵物友善班次。關於捷運動態車廂，因考量人潮及部分乘客過敏與安全顧慮，正研議於週末離峰時段之末端車廂進行限度試辦，評估報告預計下季度公布。",
    comments: [
      {
        id: "comment_3",
        author: "貓咪奴才",
        content: "雖然支持，但建議還是要區分犬貓或有隔間，有些貓咪出門看到大狗會極度恐慌。",
        createdAt: "2026-07-04T13:45:00.000Z",
        isAdmin: false
      },
      {
        id: "comment_4",
        author: "交通守護者",
        content: "支持離峰時段試辦！但飼主責任一定要落實，如果便溺或咬傷人必須有明確罰則。",
        createdAt: "2026-07-04T14:20:00.000Z",
        isAdmin: false
      }
    ]
  },
  {
    id: "wish_1719912300003",
    title: "捷運站與學校普及『雨天共享雨傘』系統",
    description: "台灣氣候潮濕多雨，午後雷陣雨常讓人措手不及。希望仿照 YouBike 模式，於各主要捷運站出口、公車轉運站、大學校園內設置自動化共享雨傘機台。前 30 分鐘免費或僅收 5 元，並可甲地租乙地還，減少一次性塑膠愛心傘的拋棄浪費。",
    expectedEffect: "讓民眾在無預警降雨時有傘可用，減少路上塑膠垃圾，推動共享環保綠色生活。",
    category: "生活便利",
    creator: "環保小尖兵",
    status: "Accepted",
    createdAt: "2026-07-03T03:15:00.000Z",
    votes: 189,
    targetVotes: 100,
    voters: [],
    officialResponse: "【環保局與捷運公司聯合公告】：本案已採納。目前正與民間共享傘業者洽談，預計於今年底前於雙北捷運精選 20 個站點率先試辦自動租借站，憑電子票證或行動支付即可免押金租借。",
    comments: [
      {
        id: "comment_5",
        author: "便利人生",
        content: "這個超需要！每次下雨都要去超商買 100 元的塑膠傘，家裡已經累積了 20 把了，真的很不環保。",
        createdAt: "2026-07-03T04:30:00.000Z",
        isAdmin: false
      }
    ]
  },
  {
    id: "wish_1719912300004",
    title: "全面推動『無障礙人行道與騎樓整平』專案",
    description: "目前許多舊社區人行道破碎不連貫，騎樓高低落差極大且停滿機車，導致輪椅族、盲胞及推嬰兒車的家長被迫走到車道上與車爭道，非常危險。建議政府提撥專款，針對學區、醫院周邊 500 公尺進行人行道拓寬與強制整平騎樓。",
    expectedEffect: "改善行人地獄污名，保障高齡化社會的長者安全，打造真正人本尊嚴的通行環境。",
    category: "公共政策",
    creator: "推車爸爸",
    status: "Proposed",
    createdAt: "2026-07-06T02:10:00.000Z",
    votes: 45,
    targetVotes: 100,
    voters: [],
    officialResponse: "",
    comments: [
      {
        id: "comment_6",
        author: "安全第一",
        content: "附議！尤其是學區附近，每次看到小學生要繞過違停走在大馬路上都捏一把冷汗。",
        createdAt: "2026-07-06T03:30:00.000Z",
        isAdmin: false
      }
    ]
  }
];

// 初始化資料庫
function initDatabase() {
  const data = localStorage.getItem(STORAGE_KEY);
  if (!data) {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(DEFAULT_WISHES));
  }
}

// 取得所有願望
function getWishes() {
  initDatabase();
  try {
    return JSON.parse(localStorage.getItem(STORAGE_KEY));
  } catch (e) {
    console.error("讀取 LocalStorage 資料失敗：", e);
    return DEFAULT_WISHES;
  }
}

// 儲存所有願望
function saveWishes(wishes) {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(wishes));
    return true;
  } catch (e) {
    console.error("儲存 LocalStorage 資料失敗：", e);
    return false;
  }
}

// 根據 ID 取得單一願望
function getWishById(id) {
  const wishes = getWishes();
  return wishes.find(w => w.id === id);
}

// 新增一個願望
function addWish(wishData) {
  const wishes = getWishes();
  const newWish = {
    id: "wish_" + Date.now(),
    title: wishData.title.trim(),
    description: wishData.description.trim(),
    expectedEffect: wishData.expectedEffect.trim(),
    category: wishData.category || "其他",
    creator: wishData.creator.trim() || "匿名市民",
    status: "Proposed", // 預設新提案是「提案中」
    createdAt: new Date().toISOString(),
    votes: 1, // 提案人自動投自己一票
    targetVotes: 100, // 門檻 100 票
    voters: [wishData.voterId || "creator_user"], // 提案人本身標記已投過票
    officialResponse: "",
    comments: []
  };
  
  wishes.unshift(newWish); // 最新的排在前面
  saveWishes(wishes);
  return newWish;
}

// 投願 / 附議
function voteWish(id, voterId) {
  const wishes = getWishes();
  const wish = wishes.find(w => w.id === id);
  if (!wish) return { success: false, message: "找不到該提案" };
  
  // 檢查是否投過票
  if (wish.voters && wish.voters.includes(voterId)) {
    return { success: false, message: "您已經為此提案投過願了！" };
  }
  
  wish.votes += 1;
  if (!wish.voters) wish.voters = [];
  wish.voters.push(voterId);
  
  // 附議進度邏輯：如果票數超過 100 票，且狀態是 Proposed 或是 Voting，自動移入 Voting 或是 Reviewing
  if (wish.votes >= wish.targetVotes && wish.status === 'Proposed') {
    wish.status = 'Voting';
  } else if (wish.votes >= wish.targetVotes && wish.status === 'Voting') {
    wish.status = 'Reviewing';
  }
  
  saveWishes(wishes);
  return { success: true, votes: wish.votes, status: wish.status, wish: wish };
}

// 新增留言
function addComment(id, commentData) {
  const wishes = getWishes();
  const wish = wishes.find(w => w.id === id);
  if (!wish) return { success: false, message: "找不到該提案" };
  
  const newComment = {
    id: "comment_" + Date.now(),
    author: commentData.author.trim() || "熱心網友",
    content: commentData.content.trim(),
    createdAt: new Date().toISOString(),
    isAdmin: !!commentData.isAdmin
  };
  
  wish.comments.push(newComment);
  saveWishes(wishes);
  return { success: true, comment: newComment, wish: wish };
}

// 小編管理員：更新願望狀態與官方回應
function updateWishStatus(id, status, officialResponse) {
  const wishes = getWishes();
  const wish = wishes.find(w => w.id === id);
  if (!wish) return { success: false, message: "找不到該提案" };
  
  wish.status = status;
  wish.officialResponse = officialResponse.trim();
  
  saveWishes(wishes);
  return { success: true, wish: wish };
}

// 導出資料層 API（於 app.js / html 中使用）
window.WishDB = {
  getWishes,
  getWishById,
  addWish,
  voteWish,
  addComment,
  updateWishStatus
};
