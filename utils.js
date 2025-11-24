const fs = require('fs');
const config = require('./config');

class Utils {
  // File Operations
  static ensureFilesExist() {
    const files = [
      './data/used_accounts.txt',
      './data/banned_users.txt', 
      './data/feedback.txt',
      './data/keys.json'
    ];

    files.forEach(file => {
      if (!fs.existsSync('./data')) fs.mkdirSync('./data');
      if (!fs.existsSync(file)) {
        if (file.endsWith('.json')) {
          fs.writeFileSync(file, JSON.stringify({ keys: {}, user_keys: {} }, null, 2));
        } else {
          fs.writeFileSync(file, '');
        }
      }
    });
  }

  static loadKeys() {
    try {
      return JSON.parse(fs.readFileSync(config.KEYS_FILE, 'utf8'));
    } catch {
      return { keys: {}, user_keys: {} };
    }
  }

  static saveKeys(data) {
    fs.writeFileSync(config.KEYS_FILE, JSON.stringify(data, null, 2));
  }

  static readUsedAccounts() {
    try {
      return new Set(fs.readFileSync(config.USED_ACCOUNTS_FILE, 'utf8').split('\n').filter(l => l));
    } catch {
      return new Set();
    }
  }

  static appendUsedAccounts(accounts) {
    fs.appendFileSync(config.USED_ACCOUNTS_FILE, accounts.join('\n') + '\n');
  }

  static readBannedUsers() {
    try {
      return new Set(fs.readFileSync(config.BANNED_USERS_FILE, 'utf8').split('\n').filter(l => l));
    } catch {
      return new Set();
    }
  }

  static banUser(userId) {
    fs.appendFileSync(config.BANNED_USERS_FILE, userId + '\n');
  }

  static unbanUser(userId) {
    const banned = this.readBannedUsers();
    banned.delete(userId.toString());
    fs.writeFileSync(config.BANNED_USERS_FILE, [...banned].join('\n'));
  }

  static appendFeedback(userId, username, feedback) {
    const time = new Date().toLocaleString();
    fs.appendFileSync(config.FEEDBACK_FILE, `[${time}] ${userId} (@${username}): ${feedback}\n`);
  }

  static clearUsedAccounts() {
    fs.writeFileSync(config.USED_ACCOUNTS_FILE, '');
  }

  // Key Generation
  static generateKey(length = 10) {
    const chars = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789";
    return "TOOLIPOP-" + Array.from({length}, () => chars[Math.floor(Math.random() * chars.length)]).join('');
  }

  static getExpiryTime(duration) {
    if (duration === "lifetime") return null;
    const durations = {
      "1m": 60, "5m": 300, "1h": 3600, "1d": 86400, 
      "3d": 259200, "7d": 604800, "15d": 1296000, "30d": 2592000
    };
    return Math.floor(Date.now() / 1000) + (durations[duration] || 0);
  }

  static formatTime(seconds) {
    if (!seconds) return "Lifetime";
    return new Date(seconds * 1000).toLocaleString();
  }

  static isExpired(expiry) {
    return expiry && Date.now() / 1000 > expiry;
  }

  // Menu Creation
  static createMainMenu(isAdmin = false) {
    const keyboard = [
      [{ text: `${config.EMOJIS.generate} GENERATE ACCOUNTS`, callback_data: "generate_menu" }],
      [
        { text: `${config.EMOJIS.info} BOT INFO`, callback_data: "bot_info" },
        { text: `${config.EMOJIS.help} HELP`, callback_data: "help" }
      ],
      [
        { text: `${config.EMOJIS.time} MY TIME`, callback_data: "my_time" },
        { text: `${config.EMOJIS.stats} STATS`, callback_data: "stats" }
      ],
      [
        { text: `${config.EMOJIS.feedback} FEEDBACK`, callback_data: "feedback" },
        { text: `${config.EMOJIS.key} REDEEM KEY`, callback_data: "redeem_info" }
      ]
    ];

    if (isAdmin) {
      keyboard.push([{ text: `${config.EMOJIS.admin} ADMIN PANEL`, callback_data: "admin_panel" }]);
    }

    return { inline_keyboard: keyboard };
  }

  static createAdminMenu() {
    return {
      inline_keyboard: [
        [
          { text: `${config.EMOJIS.key} GENERATE KEY`, callback_data: "generate_key_menu" },
          { text: `${config.EMOJIS.logs} VIEW LOGS`, callback_data: "view_logs" }
        ],
        [
          { text: `${config.EMOJIS.stats} STATISTICS`, callback_data: "admin_stats" },
          { text: `${config.EMOJIS.users} USER LIST`, callback_data: "user_list" }
        ],
        [
          { text: `${config.EMOJIS.broadcast} BROADCAST`, callback_data: "broadcast" },
          { text: `${config.EMOJIS.search} SEARCH`, callback_data: "search" }
        ],
        [
          { text: `${config.EMOJIS.ban} BAN USER`, callback_data: "ban_user" },
          { text: `${config.EMOJIS.unban} UNBAN USER`, callback_data: "unban_user" }
        ],
        [
          { text: `${config.EMOJIS.clear} CLEAR USED`, callback_data: "clear_used" },
          { text: `${config.EMOJIS.domain} DOMAINS`, callback_data: "domain_menu" }
        ],
        [{ text: `${config.EMOJIS.back} MAIN MENU`, callback_data: "main_menu" }]
      ]
    };
  }

  static createDomainMenu(prefix = "generate") {
    const keyboard = [];
    for (let i = 0; i < config.DOMAINS.length; i += 3) {
      const row = [];
      for (let j = 0; j < 3 && i + j < config.DOMAINS.length; j++) {
        row.push({ text: config.DOMAINS[i + j], callback_data: `${prefix}_${config.DOMAINS[i + j]}` });
      }
      keyboard.push(row);
    }
    keyboard.push([{ text: `${config.EMOJIS.back} BACK`, callback_data: "main_menu" }]);
    return { inline_keyboard: keyboard };
  }

  static createKeyDurationMenu() {
    return {
      inline_keyboard: [
        [
          { text: "1 MINUTE", callback_data: "key_1m" },
          { text: "1 HOUR", callback_data: "key_1h" },
          { text: "1 DAY", callback_data: "key_1d" }
        ],
        [
          { text: "3 DAYS", callback_data: "key_3d" },
          { text: "7 DAYS", callback_data: "key_7d" },
          { text: "30 DAYS", callback_data: "key_30d" }
        ],
        [{ text: "LIFETIME", callback_data: "key_lifetime" }],
        [{ text: `${config.EMOJIS.back} BACK`, callback_data: "admin_panel" }]
      ]
    };
  }

  // Search in database files
  static searchAccounts(domain, usedAccounts, maxLines = config.LINES_TO_SEND) {
    const results = [];
    
    for (const dbFile of config.DATABASE_FILES) {
      if (results.length >= maxLines) break;
      try {
        if (!fs.existsSync(dbFile)) continue;
        const content = fs.readFileSync(dbFile, 'utf8');
        const lines = content.split('\n');
        
        for (const line of lines) {
          const cleanLine = line.trim();
          if (cleanLine && 
              cleanLine.toLowerCase().includes(domain.toLowerCase()) && 
              !usedAccounts.has(cleanLine)) {
            results.push(cleanLine);
            if (results.length >= maxLines) break;
          }
        }
      } catch (error) {
        console.log(`Error reading ${dbFile}:`, error.message);
      }
    }
    
    return results;
  }

  // Create file content for download
  static createFileContent(domain, accounts, type = "GENERATED") {
    const time = new Date().toLocaleString();
    let header = "";
    
    if (type === "GENERATED") {
      header = `🔥 TOOLIPOP PREMIUM ACCOUNTS\n` +
               `📅 Generated: ${time}\n` +
               `🌐 Domain: ${domain.toUpperCase()}\n` +
               `📦 Total: ${accounts.length} accounts\n\n`;
    } else {
      header = `🔍 TOOLIPOP SEARCH RESULTS\n` +
               `📅 Searched: ${time}\n` +
               `🔎 Keyword: ${domain}\n` +
               `📦 Found: ${accounts.length} accounts\n\n`;
    }
    
    return header + accounts.join('\n');
  }
}

module.exports = Utils;
