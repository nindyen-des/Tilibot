const fs = require('fs');
const config = require('./config');
const Utils = require('./utils');

class Handlers {
  constructor(bot, keysData) {
    this.bot = bot;
    this.keysData = keysData;
    this.userStates = new Map();
  }

  isAdmin(userId) {
    return userId == config.ADMIN_ID;
  }

  isBanned(userId) {
    return Utils.readBannedUsers().has(userId.toString());
  }

  async start(msg) {
    const chatId = msg.chat.id;
    
    if (this.isBanned(chatId)) {
      return this.bot.sendMessage(chatId, `${config.EMOJIS.error} You are banned from using this bot.`);
    }

    const welcome = 
      `💎 *WELCOME TO ${config.BOT_NAME}* 💎\n\n` +
      `${config.EMOJIS.success} Premium Account Generator\n` +
      `${config.EMOJIS.success} Fast & Reliable Service\n` +
      `${config.EMOJIS.success} Multiple Domains Available\n\n` +
      `*Select an option below:*`;

    await this.bot.sendMessage(chatId, welcome, {
      reply_markup: Utils.createMainMenu(this.isAdmin(chatId)),
      parse_mode: 'Markdown'
    });
  }

  async redeemKey(msg) {
    const chatId = msg.chat.id;
    const args = msg.text.split(' ').slice(1);

    if (this.isBanned(chatId)) {
      return this.bot.sendMessage(chatId, `${config.EMOJIS.error} You are banned.`);
    }

    if (args.length !== 1) {
      return this.bot.sendMessage(chatId,
        `${config.EMOJIS.warning} *Usage:* /key <key>\n*Example:* /key TOOLIPOP-ABC123`,
        { parse_mode: 'Markdown' }
      );
    }

    const key = args[0].toUpperCase();
    
    if (!this.keysData.keys[key]) {
      return this.bot.sendMessage(chatId, `${config.EMOJIS.error} Invalid key!`);
    }

    const expiry = this.keysData.keys[key];
    if (Utils.isExpired(expiry)) {
      delete this.keysData.keys[key];
      Utils.saveKeys(this.keysData);
      return this.bot.sendMessage(chatId, `${config.EMOJIS.error} Key expired!`);
    }

    this.keysData.user_keys[chatId] = expiry;
    delete this.keysData.keys[key];
    Utils.saveKeys(this.keysData);

    const expiryText = Utils.formatTime(expiry);
    
    await this.bot.sendMessage(chatId,
      `${config.EMOJIS.success} *KEY REDEEMED!*\n\n` +
      `${config.EMOJIS.key} Key: \`${key}\`\n` +
      `${config.EMOJIS.time} Expires: \`${expiryText}\`\n\n` +
      `You can now generate premium accounts!`,
      { parse_mode: 'Markdown' }
    );
  }

  async handleCallback(query) {
    const chatId = query.message.chat.id;
    const data = query.data;
    const userId = query.from.id;

    if (this.isBanned(chatId)) {
      await this.bot.answerCallbackQuery(query.id);
      return this.bot.sendMessage(chatId, `${config.EMOJIS.error} You are banned.`);
    }

    try {
      await this.bot.answerCallbackQuery(query.id);

      // Main menu handlers
      if (data === 'main_menu') await this.showMainMenu(query);
      else if (data === 'generate_menu') await this.showGenerateMenu(query);
      else if (data === 'bot_info') await this.showBotInfo(query);
      else if (data === 'help') await this.showHelp(query);
      else if (data === 'my_time') await this.showMyTime(query);
      else if (data === 'stats') await this.showStats(query);
      else if (data === 'feedback') await this.showFeedbackMenu(query);
      else if (data === 'redeem_info') await this.showRedeemInfo(query);
      
      // Admin handlers
      else if (data === 'admin_panel') await this.showAdminPanel(query);
      else if (data === 'generate_key_menu') await this.showKeyDurationMenu(query);
      else if (data === 'view_logs') await this.showLogs(query);
      else if (data === 'admin_stats') await this.showAdminStats(query);
      else if (data === 'user_list') await this.showUserList(query);
      else if (data === 'broadcast') await this.startBroadcast(query);
      else if (data === 'search') await this.startSearch(query);
      else if (data === 'ban_user') await this.startBanUser(query);
      else if (data === 'unban_user') await this.startUnbanUser(query);
      else if (data === 'clear_used') await this.clearUsedAccounts(query);
      else if (data === 'domain_menu') await this.showDomainManager(query);
      
      // Key generation
      else if (data.startsWith('key_')) await this.generateKey(query);
      
      // Account generation
      else if (data.startsWith('generate_')) await this.generateAccounts(query);
      
      // Domain management
      else if (data.startsWith('add_domain_')) await this.addDomain(query);
      else if (data.startsWith('remove_domain_')) await this.removeDomain(query);

    } catch (error) {
      console.error('Callback error:', error);
      await this.bot.sendMessage(chatId, `${config.EMOJIS.error} Error: ${error.message}`);
    }
  }

  async showMainMenu(query) {
    await this.bot.editMessageText(
      `💎 *${config.BOT_NAME}* 💎\n\nSelect an option:`,
      {
        chat_id: query.message.chat.id,
        message_id: query.message.message_id,
        reply_markup: Utils.createMainMenu(this.isAdmin(query.from.id)),
        parse_mode: 'Markdown'
      }
    );
  }

  async showGenerateMenu(query) {
    const chatId = query.message.chat.id.toString();
    
    if (!this.keysData.user_keys[chatId]) {
      return this.bot.editMessageText(
        `${config.EMOJIS.error} You need a valid key to generate accounts!\n\nUse /key <your_key> to redeem.`,
        {
          chat_id: query.message.chat.id,
          message_id: query.message.message_id,
          parse_mode: 'Markdown'
        }
      );
    }

    await this.bot.editMessageText(
      `${config.EMOJIS.generate} *SELECT DOMAIN:*`,
      {
        chat_id: query.message.chat.id,
        message_id: query.message.message_id,
        reply_markup: Utils.createDomainMenu(),
        parse_mode: 'Markdown'
      }
    );
  }

  async generateAccounts(query) {
    const chatId = query.message.chat.id.toString();
    const domain = query.data.replace('generate_', '');
    
    if (!this.keysData.user_keys[chatId]) {
      await this.bot.sendMessage(chatId, `${config.EMOJIS.error} No active key found!`);
      return;
    }

    const processingMsg = await this.bot.sendMessage(
      chatId, 
      `${config.EMOJIS.generate} Generating ${domain} accounts...`
    );

    try {
      const usedAccounts = Utils.readUsedAccounts();
      const accounts = Utils.searchAccounts(domain, usedAccounts);

      if (accounts.length === 0) {
        await this.bot.editMessageText(
          `${config.EMOJIS.error} No accounts found for *${domain}*`,
          {
            chat_id: chatId,
            message_id: processingMsg.message_id,
            parse_mode: 'Markdown'
          }
        );
        return;
      }

      Utils.appendUsedAccounts(accounts);

      const filename = `./data/${domain}_${Date.now()}.txt`;
      const content = Utils.createFileContent(domain, accounts);
      fs.writeFileSync(filename, content);

      // 2-second delay as in Python version
      await new Promise(resolve => setTimeout(resolve, 2000));

      await this.bot.deleteMessage(chatId, processingMsg.message_id);

      await this.bot.sendDocument(
        chatId,
        filename,
        {
          caption: 
            `${config.EMOJIS.success} *${domain.toUpperCase()} ACCOUNTS*\n\n` +
            `📦 *Total:* ${accounts.length} accounts\n` +
            `⏰ *Generated:* ${new Date().toLocaleString()}\n\n` +
            `${config.EMOJIS.warning} *Note:* Please use responsibly!`,
          parse_mode: 'Markdown'
        }
      );

      fs.unlinkSync(filename);

    } catch (error) {
      await this.bot.editMessageText(
        `${config.EMOJIS.error} Generation failed: ${error.message}`,
        {
          chat_id: chatId,
          message_id: processingMsg.message_id
        }
      );
    }
  }

  async showBotInfo(query) {
    const totalUsers = Object.keys(this.keysData.user_keys).length;
    const activeUsers = Object.values(this.keysData.user_keys).filter(exp => !Utils.isExpired(exp)).length;

    const info = 
      `💎 *${config.BOT_NAME}* 💎\n\n` +
      `${config.EMOJIS.success} *Version:* 3.0 Premium\n` +
      `${config.EMOJIS.developer} *Developer:* @ToolipopAdmin\n` +
      `${config.EMOJIS.domain} *Domains:* ${config.DOMAINS.length}\n` +
      `${config.EMOJIS.users} *Total Users:* ${totalUsers}\n` +
      `${config.EMOJIS.users} *Active Users:* ${activeUsers}\n\n` +
      `${config.EMOJIS.success} Fast & reliable service\n` +
      `${config.EMOJIS.success} Regular database updates\n` +
      `${config.EMOJIS.success} Premium quality accounts`;

    await this.bot.editMessageText(
      info,
      {
        chat_id: query.message.chat.id,
        message_id: query.message.message_id,
        reply_markup: { inline_keyboard: [[{ text: `${config.EMOJIS.back} BACK`, callback_data: "main_menu" }]] },
        parse_mode: 'Markdown'
      }
    );
  }

  async showHelp(query) {
    const helpText = 
      `${config.EMOJIS.help} *HELP CENTER*\n\n` +
      `${config.EMOJIS.success} */start* - Main menu\n` +
      `${config.EMOJIS.success} */key <key>* - Redeem access key\n` +
      `${config.EMOJIS.success} */generate* - Generate accounts\n\n` +
      `${config.EMOJIS.warning} *How to use:*\n` +
      `1. Get key from admin\n` +
      `2. Redeem with /key\n` +
      `3. Generate accounts\n\n` +
      `${config.EMOJIS.error} *Rules:*\n` +
      `• Don't share your key\n` +
      `• Use responsibly\n` +
      `• Report issues to admin`;

    await this.bot.editMessageText(
      helpText,
      {
        chat_id: query.message.chat.id,
        message_id: query.message.message_id,
        reply_markup: { inline_keyboard: [[{ text: `${config.EMOJIS.back} BACK`, callback_data: "main_menu" }]] },
        parse_mode: 'Markdown'
      }
    );
  }

  async showMyTime(query) {
    const chatId = query.message.chat.id.toString();
    const expiry = this.keysData.user_keys[chatId];

    if (!expiry) {
      await this.bot.editMessageText(
        `${config.EMOJIS.error} No active key found!\n\nRedeem a key first.`,
        {
          chat_id: query.message.chat.id,
          message_id: query.message.message_id,
          parse_mode: 'Markdown'
        }
      );
      return;
    }

    const expiryText = Utils.formatTime(expiry);
    const status = Utils.isExpired(expiry) ? "EXPIRED" : "ACTIVE";

    await this.bot.editMessageText(
      `${config.EMOJIS.time} *ACCOUNT STATUS*\n\n` +
      `${config.EMOJIS.success} User: \`${chatId}\`\n` +
      `${config.EMOJIS.success} Status: \`${status}\`\n` +
      `${config.EMOJIS.time} Expires: \`${expiryText}\``,
      {
        chat_id: query.message.chat.id,
        message_id: query.message.message_id,
        reply_markup: { 
          inline_keyboard: [
            [{ text: `${config.EMOJIS.generate} GENERATE`, callback_data: "generate_menu" }],
            [{ text: `${config.EMOJIS.back} BACK`, callback_data: "main_menu" }]
          ]
        },
        parse_mode: 'Markdown'
      }
    );
  }

  async showStats(query) {
    const totalUsers = Object.keys(this.keysData.user_keys).length;
    const activeUsers = Object.values(this.keysData.user_keys).filter(exp => !Utils.isExpired(exp)).length;
    const expiredUsers = totalUsers - activeUsers;

    await this.bot.editMessageText(
      `${config.EMOJIS.stats} *BOT STATISTICS*\n\n` +
      `${config.EMOJIS.users} Total Users: \`${totalUsers}\`\n` +
      `${config.EMOJIS.success} Active Users: \`${activeUsers}\`\n` +
      `${config.EMOJIS.error} Expired Users: \`${expiredUsers}\`\n` +
      `${config.EMOJIS.key} Available Keys: \`${Object.keys(this.keysData.keys).length}\`\n` +
      `${config.EMOJIS.domain} Domains: \`${config.DOMAINS.length}\``,
      {
        chat_id: query.message.chat.id,
        message_id: query.message.message_id,
        reply_markup: { inline_keyboard: [[{ text: `${config.EMOJIS.back} BACK`, callback_data: "main_menu" }]] },
        parse_mode: 'Markdown'
      }
    );
  }

  async showFeedbackMenu(query) {
    await this.bot.editMessageText(
      `${config.EMOJIS.feedback} *FEEDBACK*\n\nSend your message below:`,
      {
        chat_id: query.message.chat.id,
        message_id: query.message.message_id,
        reply_markup: { inline_keyboard: [[{ text: `${config.EMOJIS.back} BACK`, callback_data: "main_menu" }]] },
        parse_mode: 'Markdown'
      }
    );
    
    this.userStates.set(query.from.id, 'awaiting_feedback');
  }

  async showRedeemInfo(query) {
    await this.bot.editMessageText(
      `${config.EMOJIS.key} *REDEEM KEY*\n\n` +
      `Usage: /key <your_key>\n\n` +
      `Example: /key TOOLIPOP-ABC123DEF45\n\n` +
      `Get keys from admin: @ToolipopAdmin`,
      {
        chat_id: query.message.chat.id,
        message_id: query.message.message_id,
        reply_markup: { inline_keyboard: [[{ text: `${config.EMOJIS.back} BACK`, callback_data: "main_menu" }]] },
        parse_mode: 'Markdown'
      }
    );
  }

  // ADMIN HANDLERS
  async showAdminPanel(query) {
    if (!this.isAdmin(query.from.id)) {
      return this.bot.editMessageText(
        `${config.EMOJIS.error} Access denied!`,
        {
          chat_id: query.message.chat.id,
          message_id: query.message.message_id
        }
      );
    }

    await this.bot.editMessageText(
      `${config.EMOJIS.admin} *ADMIN PANEL*\n\nManage your bot:`,
      {
        chat_id: query.message.chat.id,
        message_id: query.message.message_id,
        reply_markup: Utils.createAdminMenu(),
        parse_mode: 'Markdown'
      }
    );
  }

  async showKeyDurationMenu(query) {
    if (!this.isAdmin(query.from.id)) return;
    
    await this.bot.editMessageText(
      `${config.EMOJIS.key} *SELECT KEY DURATION:*`,
      {
        chat_id: query.message.chat.id,
        message_id: query.message.message_id,
        reply_markup: Utils.createKeyDurationMenu(),
        parse_mode: 'Markdown'
      }
    );
  }

  async generateKey(query) {
    if (!this.isAdmin(query.from.id)) return;

    const duration = query.data.replace('key_', '');
    const key = Utils.generateKey();
    const expiry = Utils.getExpiryTime(duration);

    this.keysData.keys[key] = expiry;
    Utils.saveKeys(this.keysData);

    await this.bot.editMessageText(
      `${config.EMOJIS.success} *KEY GENERATED!*\n\n` +
      `${config.EMOJIS.key} Key: \`${key}\`\n` +
      `${config.EMOJIS.time} Duration: \`${duration}\`\n\n` +
      `Share this key with users.`,
      {
        chat_id: query.message.chat.id,
        message_id: query.message.message_id,
        parse_mode: 'Markdown'
      }
    );
  }

  async showLogs(query) {
    if (!this.isAdmin(query.from.id)) return;

    const users = Object.entries(this.keysData.user_keys);
    
    if (users.length === 0) {
      return this.bot.editMessageText(
        `${config.EMOJIS.warning} No users yet.`,
        {
          chat_id: query.message.chat.id,
          message_id: query.message.message_id
        }
      );
    }

    let logText = `${config.EMOJIS.logs} *USER LOGS:*\n\n`;
    users.forEach(([user, expiry]) => {
      const expiryText = Utils.formatTime(expiry);
      logText += `👤 ${user} - ⏰ ${expiryText}\n`;
    });

    await this.bot.editMessageText(
      logText,
      {
        chat_id: query.message.chat.id,
        message_id: query.message.message_id,
        reply_markup: { inline_keyboard: [[{ text: `${config.EMOJIS.back} BACK`, callback_data: "admin_panel" }]] },
        parse_mode: 'Markdown'
      }
    );
  }

  async showAdminStats(query) {
    if (!this.isAdmin(query.from.id)) return;

    const totalUsers = Object.keys(this.keysData.user_keys).length;
    const activeUsers = Object.values(this.keysData.user_keys).filter(exp => !Utils.isExpired(exp)).length;
    const expiredUsers = totalUsers - activeUsers;
    const bannedUsers = Utils.readBannedUsers().size;

    await this.bot.editMessageText(
      `${config.EMOJIS.stats} *ADMIN STATS*\n\n` +
      `${config.EMOJIS.users} Total Users: \`${totalUsers}\`\n` +
      `${config.EMOJIS.success} Active: \`${activeUsers}\`\n` +
      `${config.EMOJIS.error} Expired: \`${expiredUsers}\`\n` +
      `${config.EMOJIS.ban} Banned: \`${bannedUsers}\`\n` +
      `${config.EMOJIS.key} Available Keys: \`${Object.keys(this.keysData.keys).length}\`\n` +
      `${config.EMOJIS.domain} Domains: \`${config.DOMAINS.length}\``,
      {
        chat_id: query.message.chat.id,
        message_id: query.message.message_id,
        reply_markup: { inline_keyboard: [[{ text: `${config.EMOJIS.back} BACK`, callback_data: "admin_panel" }]] },
        parse_mode: 'Markdown'
      }
    );
  }

  async showUserList(query) {
    if (!this.isAdmin(query.from.id)) return;

    const users = Object.entries(this.keysData.user_keys);
    
    if (users.length === 0) {
      return this.bot.editMessageText(
        `${config.EMOJIS.warning} No users found.`,
        {
          chat_id: query.message.chat.id,
          message_id: query.message.message_id,
          reply_markup: { inline_keyboard: [[{ text: `${config.EMOJIS.back} BACK`, callback_data: "admin_panel" }]] }
        }
      );
    }

    // Send in chunks of 30 users
    const chunkSize = 30;
    for (let i = 0; i < users.length; i += chunkSize) {
      const chunk = users.slice(i, i + chunkSize);
      let userList = `${config.EMOJIS.users} *USERS (${i+1}-${Math.min(i+chunkSize, users.length)}/${users.length})*\n\n`;
      
      chunk.forEach(([user, expiry], index) => {
        const status = Utils.isExpired(expiry) ? "EXPIRED" : "ACTIVE";
        userList += `${i + index + 1}. ${user} - ${status}\n`;
      });

      const keyboard = i + chunkSize >= users.length ? 
        { inline_keyboard: [[{ text: `${config.EMOJIS.back} BACK`, callback_data: "admin_panel" }]] } : undefined;

      if (i === 0) {
        await this.bot.editMessageText(userList, {
          chat_id: query.message.chat.id,
          message_id: query.message.message_id,
          reply_markup: keyboard,
          parse_mode: 'Markdown'
        });
      } else {
        await this.bot.sendMessage(query.message.chat.id, userList, {
          reply_markup: keyboard,
          parse_mode: 'Markdown'
        });
      }
    }
  }

  async startBroadcast(query) {
    if (!this.isAdmin(query.from.id)) return;
    
    await this.bot.editMessageText(
      `${config.EMOJIS.broadcast} *BROADCAST MESSAGE*\n\nReply with your message:`,
      {
        chat_id: query.message.chat.id,
        message_id: query.message.message_id,
        parse_mode: 'Markdown'
      }
    );
    
    this.userStates.set(query.from.id, 'awaiting_broadcast');
  }

  async startSearch(query) {
    if (!this.isAdmin(query.from.id)) return;
    
    await this.bot.editMessageText(
      `${config.EMOJIS.search} *SEARCH ACCOUNTS*\n\nFormat: <keyword> <limit>\nExample: garena 50`,
      {
        chat_id: query.message.chat.id,
        message_id: query.message.message_id,
        parse_mode: 'Markdown'
      }
    );
    
    this.userStates.set(query.from.id, 'awaiting_search');
  }

  async startBanUser(query) {
    if (!this.isAdmin(query.from.id)) return;
    
    await this.bot.editMessageText(
      `${config.EMOJIS.ban} *BAN USER*\n\nReply with user ID:`,
      {
        chat_id: query.message.chat.id,
        message_id: query.message.message_id,
        parse_mode: 'Markdown'
      }
    );
    
    this.userStates.set(query.from.id, 'awaiting_ban');
  }

  async startUnbanUser(query) {
    if (!this.isAdmin(query.from.id)) return;
    
    await this.bot.editMessageText(
      `${config.EMOJIS.unban} *UNBAN USER*\n\nReply with user ID:`,
      {
        chat_id: query.message.chat.id,
        message_id: query.message.message_id,
        parse_mode: 'Markdown'
      }
    );
    
    this.userStates.set(query.from.id, 'awaiting_unban');
  }

  async clearUsedAccounts(query) {
    if (!this.isAdmin(query.from.id)) return;
    
    Utils.clearUsedAccounts();
    
    await this.bot.editMessageText(
      `${config.EMOJIS.success} Used accounts cleared!`,
      {
        chat_id: query.message.chat.id,
        message_id: query.message.message_id,
        reply_markup: { inline_keyboard: [[{ text: `${config.EMOJIS.back} BACK`, callback_data: "admin_panel" }]] }
      }
    );
  }

  async showDomainManager(query) {
    if (!this.isAdmin(query.from.id)) return;

    const keyboard = {
      inline_keyboard: [
        [{ text: `${config.EMOJIS.add} ADD DOMAIN`, callback_data: "add_domain_start" }],
        [{ text: `${config.EMOJIS.remove} REMOVE DOMAIN`, callback_data: "remove_domain_start" }],
        [{ text: `${config.EMOJIS.back} BACK`, callback_data: "admin_panel" }]
      ]
    };

    await this.bot.editMessageText(
      `${config.EMOJIS.domain} *DOMAIN MANAGER*\n\nCurrent domains: ${config.DOMAINS.join(', ')}`,
      {
        chat_id: query.message.chat.id,
        message_id: query.message.message_id,
        reply_markup: keyboard,
        parse_mode: 'Markdown'
      }
    );
  }

  async addDomain(query) {
    if (!this.isAdmin(query.from.id)) return;
    
    if (query.data === 'add_domain_start') {
      await this.bot.editMessageText(
        `${config.EMOJIS.add} *ADD DOMAIN*\n\nReply with new domain name:`,
        {
          chat_id: query.message.chat.id,
          message_id: query.message.message_id,
          parse_mode: 'Markdown'
        }
      );
      this.userStates.set(query.from.id, 'awaiting_add_domain');
    }
  }

  async removeDomain(query) {
    if (!this.isAdmin(query.from.id)) return;
    
    if (query.data === 'remove_domain_start') {
      await this.bot.editMessageText(
        `${config.EMOJIS.remove} *REMOVE DOMAIN*\n\nReply with domain to remove:`,
        {
          chat_id: query.message.chat.id,
          message_id: query.message.message_id,
          parse_mode: 'Markdown'
        }
      );
      this.userStates.set(query.from.id, 'awaiting_remove_domain');
    }
  }

  // Handle text messages (for conversations)
  async handleTextMessage(msg) {
    const userId = msg.from.id;
    const chatId = msg.chat.id;
    const text = msg.text;

    if (!this.userStates.has(userId)) return;

    const state = this.userStates.get(userId);
    this.userStates.delete(userId);

    try {
      switch (state) {
        case 'awaiting_feedback':
          await this.processFeedback(msg, text);
          break;
        case 'awaiting_broadcast':
          await this.processBroadcast(msg, text);
          break;
        case 'awaiting_search':
          await this.processSearch(msg, text);
          break;
        case 'awaiting_ban':
          await this.processBan(msg, text);
          break;
        case 'awaiting_unban':
          await this.processUnban(msg, text);
          break;
        case 'awaiting_add_domain':
          await this.processAddDomain(msg, text);
          break;
        case 'awaiting_remove_domain':
          await this.processRemoveDomain(msg, text);
          break;
      }
    } catch (error) {
      await this.bot.sendMessage(chatId, `${config.EMOJIS.error} Error: ${error.message}`);
    }
  }

  async processFeedback(msg, text) {
    const username = msg.from.username || 'NoUsername';
    Utils.appendFeedback(msg.chat.id, username, text);
    
    await this.bot.sendMessage(
      msg.chat.id,
      `${config.EMOJIS.success} Feedback sent to admin!`,
      { reply_markup: Utils.createMainMenu(this.isAdmin(msg.chat.id)) }
    );

    // Notify admin
    await this.bot.sendMessage(
      config.ADMIN_ID,
      `${config.EMOJIS.feedback} *NEW FEEDBACK*\n\nFrom: ${msg.chat.id} (@${username})\nMessage: ${text}`,
      { parse_mode: 'Markdown' }
    );
  }

  async processBroadcast(msg, text) {
    if (!this.isAdmin(msg.from.id)) return;

    const users = Object.keys(this.keysData.user_keys);
    let success = 0, failed = 0;

    const statusMsg = await this.bot.sendMessage(msg.chat.id, `${config.EMOJIS.broadcast} Sending to ${users.length} users...`);

    for (const userId of users) {
      try {
        await this.bot.sendMessage(userId, 
          `${config.EMOJIS.broadcast} *BROADCAST*\n\n${text}`,
          { parse_mode: 'Markdown' }
        );
        success++;
        await new Promise(resolve => setTimeout(resolve, 100)); // Rate limiting
      } catch (error) {
        failed++;
      }
    }

    await this.bot.editMessageText(
      `${config.EMOJIS.success} *BROADCAST COMPLETE*\n\n✅ Success: ${success}\n❌ Failed: ${failed}`,
      {
        chat_id: msg.chat.id,
        message_id: statusMsg.message_id,
        reply_markup: { inline_keyboard: [[{ text: `${config.EMOJIS.back} ADMIN`, callback_data: "admin_panel" }]] },
        parse_mode: 'Markdown'
      }
    );
  }

  async processSearch(msg, text) {
    if (!this.isAdmin(msg.from.id)) return;

    const parts = text.split(' ');
    const keyword = parts[0];
    const limit = parseInt(parts[1]) || 100;

    const statusMsg = await this.bot.sendMessage(msg.chat.id, `${config.EMOJIS.search} Searching for "${keyword}"...`);

    const usedAccounts = Utils.readUsedAccounts();
    const results = Utils.searchAccounts(keyword, usedAccounts, limit);

    if (results.length === 0) {
      await this.bot.editMessageText(
        `${config.EMOJIS.error} No accounts found for "${keyword}"`,
        { chat_id: msg.chat.id, message_id: statusMsg.message_id }
      );
      return;
    }

    const filename = `./data/search_${Date.now()}.txt`;
    const content = Utils.createFileContent(keyword, results, "SEARCH");
    fs.writeFileSync(filename, content);

    await this.bot.deleteMessage(msg.chat.id, statusMsg.message_id);

    await this.bot.sendDocument(
      msg.chat.id,
      filename,
      {
        caption: `${config.EMOJIS.success} Found ${results.length} accounts for "${keyword}"`,
        parse_mode: 'Markdown'
      }
    );

    fs.unlinkSync(filename);
  }

  async processBan(msg, text) {
    if (!this.isAdmin(msg.from.id)) return;

    const userId = text.trim();
    if (!userId.match(/^\d+$/)) {
      return this.bot.sendMessage(msg.chat.id, `${config.EMOJIS.error} Invalid user ID!`);
    }

    Utils.banUser(userId);
    await this.bot.sendMessage(
      msg.chat.id,
      `${config.EMOJIS.success} User ${userId} banned!`,
      { reply_markup: Utils.createAdminMenu() }
    );
  }

  async processUnban(msg, text) {
    if (!this.isAdmin(msg.from.id)) return;

    const userId = text.trim();
    if (!userId.match(/^\d+$/)) {
      return this.bot.sendMessage(msg.chat.id, `${config.EMOJIS.error} Invalid user ID!`);
    }

    Utils.unbanUser(userId);
    await this.bot.sendMessage(
      msg.chat.id,
      `${config.EMOJIS.success} User ${userId} unbanned!`,
      { reply_markup: Utils.createAdminMenu() }
    );
  }

  async processAddDomain(msg, text) {
    if (!this.isAdmin(msg.from.id)) return;

    const domain = text.trim().toLowerCase();
    if (config.DOMAINS.includes(domain)) {
      return this.bot.sendMessage(msg.chat.id, `${config.EMOJIS.error} Domain already exists!`);
    }

    config.DOMAINS.push(domain);
    await this.bot.sendMessage(
      msg.chat.id,
      `${config.EMOJIS.success} Domain "${domain}" added!`,
      { reply_markup: Utils.createAdminMenu() }
    );
  }

  async processRemoveDomain(msg, text) {
    if (!this.isAdmin(msg.from.id)) return;

    const domain = text.trim().toLowerCase();
    const index = config.DOMAINS.indexOf(domain);
    
    if (index === -1) {
      return this.bot.sendMessage(msg.chat.id, `${config.EMOJIS.error} Domain not found!`);
    }

    config.DOMAINS.splice(index, 1);
    await this.bot.sendMessage(
      msg.chat.id,
      `${config.EMOJIS.success} Domain "${domain}" removed!`,
      { reply_markup: Utils.createAdminMenu() }
    );
  }
}

module.exports = Handlers;
