const TelegramBot = require('node-telegram-bot-api');
const express = require('express');

// === CONFIGURATION ===
const TOKEN = process.env.BOT_TOKEN || '8551305615:AAEdnWWsmqoWTT_pqiCQd-qO__LyVK7HG8E';
const ADMIN_ID = parseInt(process.env.ADMIN_ID) || 7472543084; // PALITAN MO ITO NG ID MO
const PORT = process.env.PORT || 3000;

// === SIMPLE DATABASE ===
const accountsDB = {
  'garena': [
    'garena_user1:password123',
    'garena_user2:password456',
    'garena_user3:password789'
  ],
  'roblox': [
    'roblox_user1:pass123',
    'roblox_user2:pass456', 
    'roblox_user3:pass789'
  ],
  'mobilelegends': [
    'ml_user1:pass123',
    'ml_user2:pass456',
    'ml_user3:pass789'
  ],
  'freefire': [
    'ff_user1:pass123',
    'ff_user2:pass456',
    'ff_user3:pass789'
  ]
};

const keysDB = {};
const userKeys = {};
const bannedUsers = new Set();

// === EMOJIS ===
const EMOJIS = {
  main: '🌟',
  generate: '🔍',
  admin: '🛠',
  info: 'ℹ️',
  help: '🆘',
  success: '✅',
  error: '❌',
  key: '🔑',
  back: '🔙'
};

// === UTILITY FUNCTIONS ===
function generateRandomKey(length = 8) {
  const chars = 'ABCDEFGHJKLMNPQRSTUVWXYZ23456789';
  return 'TOLLIPOP-' + Array.from({length}, () => 
    chars[Math.floor(Math.random() * chars.length)]
  ).join('');
}

function isAdmin(userId) {
  return userId === ADMIN_ID;
}

// === CREATE BOT ===
const bot = new TelegramBot(TOKEN, {polling: true});

// === COMMAND HANDLERS ===
bot.onText(/\/start/, (msg) => {
  const chatId = msg.chat.id;
  const userId = msg.from.id;
  
  if (bannedUsers.has(userId)) {
    return bot.sendMessage(chatId, `${EMOJIS.error} You have been banned from using this bot.`);
  }
  
  const keyboard = {
    reply_markup: {
      inline_keyboard: [
        [{ text: `${EMOJIS.generate} Generate Accounts`, callback_data: 'main_generate' }],
        [{ text: `${EMOJIS.info} Bot Info`, callback_data: 'main_info' }, 
         { text: `${EMOJIS.help} Help`, callback_data: 'main_help' }],
        [{ text: `${EMOJIS.key} Redeem Key`, callback_data: 'main_redeem' }]
      ]
    }
  };
  
  // Add admin panel for admin
  if (isAdmin(userId)) {
    keyboard.reply_markup.inline_keyboard.push(
      [{ text: `${EMOJIS.admin} ADMIN PANEL`, callback_data: 'main_admin' }]
    );
  }
  
  const welcomeMessage = `${EMOJIS.main} *𝗪𝗘𝗟𝗖𝗢𝗠𝗘 𝗧𝗢 𝗧𝗢𝗟𝗟𝗜𝗣𝗢𝗣 𝗙𝗥𝗘𝗘 𝗕𝗢𝗧!* ${EMOJIS.main}\n\n${EMOJIS.success} Generate premium accounts with ease\n${EMOJIS.success} Fast and reliable service\n${EMOJIS.success} Multiple domains available\n\nSelect an option below:`;
  
  bot.sendMessage(chatId, welcomeMessage, { 
    parse_mode: 'Markdown',
    ...keyboard
  });
});

bot.onText(/\/key (.+)/, (msg, match) => {
  const chatId = msg.chat.id;
  const userId = msg.from.id;
  const enteredKey = match[1].toUpperCase();
  
  if (bannedUsers.has(userId)) {
    return bot.sendMessage(chatId, `${EMOJIS.error} You have been banned from using this bot.`);
  }
  
  if (!keysDB[enteredKey]) {
    return bot.sendMessage(chatId, `${EMOJIS.error} Invalid or expired key!`);
  }
  
  userKeys[userId] = keysDB[enteredKey];
  delete keysDB[enteredKey];
  
  const keyboard = {
    reply_markup: {
      inline_keyboard: [
        [{ text: `${EMOJIS.generate} Generate Accounts`, callback_data: 'main_generate' }]
      ]
    }
  };
  
  bot.sendMessage(chatId, 
    `${EMOJIS.success} *Key Redeemed Successfully!*\n\n${EMOJIS.key} Key: \`${enteredKey}\`\n${EMOJIS.success} You can now generate premium accounts!`,
    { parse_mode: 'Markdown', ...keyboard }
  );
});

bot.onText(/\/help/, (msg) => {
  const chatId = msg.chat.id;
  const helpText = `${EMOJIS.help} *Help Center* ${EMOJIS.help}\n\n${EMOJIS.success} */start* - Show main menu\n${EMOJIS.success} */key <key>* - Redeem your access key\n${EMOJIS.success} Use the generate button to get accounts\n\n${EMOJIS.success} *How to use:*\n1. Get an access key from admin\n2. Redeem it using /key command\n3. Use the generate button to get accounts`;
  
  bot.sendMessage(chatId, helpText, { parse_mode: 'Markdown' });
});

// === CALLBACK QUERY HANDLERS ===
bot.on('callback_query', (callbackQuery) => {
  const msg = callbackQuery.message;
  const data = callbackQuery.data;
  const userId = callbackQuery.from.id;
  const chatId = msg.chat.id;
  
  bot.answerCallbackQuery(callbackQuery.id);
  
  // Main menu handler
  if (data === 'main_menu') {
    const keyboard = {
      reply_markup: {
        inline_keyboard: [
          [{ text: `${EMOJIS.generate} Generate Accounts`, callback_data: 'main_generate' }],
          [{ text: `${EMOJIS.info} Bot Info`, callback_data: 'main_info' }, 
           { text: `${EMOJIS.help} Help`, callback_data: 'main_help' }],
          [{ text: `${EMOJIS.key} Redeem Key`, callback_data: 'main_redeem' }]
        ]
      }
    };
    
    if (isAdmin(userId)) {
      keyboard.reply_markup.inline_keyboard.push(
        [{ text: `${EMOJIS.admin} ADMIN PANEL`, callback_data: 'main_admin' }]
      );
    }
    
    bot.editMessageText(`${EMOJIS.main} *𝗧𝗢𝗟𝗟𝗜𝗣𝗢𝗣 𝗔𝗖𝗖𝗢𝗨𝗡𝗧 𝗚𝗘𝗡𝗘𝗥𝗔𝗧𝗢𝗥 𝗕𝗢𝗧* ${EMOJIS.main}\n\nSelect an option below:`, {
      chat_id: chatId,
      message_id: msg.message_id,
      parse_mode: 'Markdown',
      ...keyboard
    });
    return;
  }
  
  // Generate menu
  if (data === 'main_generate') {
    if (bannedUsers.has(userId)) {
      return bot.sendMessage(chatId, `${EMOJIS.error} You have been banned from using this bot.`);
    }
    
    if (!userKeys[userId]) {
      return bot.sendMessage(chatId, `${EMOJIS.error} You need a valid key to use this feature!`);
    }
    
    const keyboard = {
      reply_markup: {
        inline_keyboard: [
          [{ text: 'Garena', callback_data: 'generate_garena' }, 
           { text: 'Roblox', callback_data: 'generate_roblox' }],
          [{ text: 'Mobile Legends', callback_data: 'generate_mobilelegends' }, 
           { text: 'Free Fire', callback_data: 'generate_freefire' }],
          [{ text: `${EMOJIS.back} Main Menu`, callback_data: 'main_menu' }]
        ]
      }
    };
    
    bot.editMessageText(`${EMOJIS.generate} *Select a platform to generate:*`, {
      chat_id: chatId,
      message_id: msg.message_id,
      parse_mode: 'Markdown',
      ...keyboard
    });
    return;
  }
  
  // Generate accounts
  if (data.startsWith('generate_')) {
    const platform = data.replace('generate_', '');
    
    if (bannedUsers.has(userId)) {
      return bot.sendMessage(chatId, `${EMOJIS.error} You have been banned from using this bot.`);
    }
    
    if (!userKeys[userId]) {
      return bot.sendMessage(chatId, `${EMOJIS.error} You need a valid key to use this feature!`);
    }
    
    if (accountsDB[platform] && accountsDB[platform].length > 0) {
      const account = accountsDB[platform].shift(); // Remove first account
      const accountText = `${EMOJIS.success} *${platform.toUpperCase()} Account Generated!*\n\n\`${account}\`\n\n${EMOJIS.success} Enjoy your account!`;
      
      bot.editMessageText(accountText, {
        chat_id: chatId,
        message_id: msg.message_id,
        parse_mode: 'Markdown'
      });
    } else {
      bot.editMessageText(`${EMOJIS.error} *No available accounts found for ${platform}!*`, {
        chat_id: chatId,
        message_id: msg.message_id,
        parse_mode: 'Markdown'
      });
    }
    return;
  }
  
  // Bot info
  if (data === 'main_info') {
    const totalUsers = Object.keys(userKeys).length;
    const infoText = `${EMOJIS.info} *𝗧𝗢𝗟𝗟𝗜𝗣𝗢𝗣 𝗔𝗖𝗖𝗢𝗨𝗡𝗧 𝗚𝗘𝗡𝗘𝗥𝗔𝗧𝗢𝗥 𝗕𝗢𝗧*\n\n${EMOJIS.success} *Version:* 2.0 Simple\n${EMOJIS.success} *Developer:* @TollipopBot\n${EMOJIS.success} *Platforms Available:* ${Object.keys(accountsDB).length}\n${EMOJIS.success} *Total Users:* ${totalUsers}\n\n${EMOJIS.success} Fast and reliable account generation\n${EMOJIS.success} Secure and private\n${EMOJIS.success} Regular database updates`;
    
    const keyboard = {
      reply_markup: {
        inline_keyboard: [
          [{ text: `${EMOJIS.back} Main Menu`, callback_data: 'main_menu' }]
        ]
      }
    };
    
    bot.editMessageText(infoText, {
      chat_id: chatId,
      message_id: msg.message_id,
      parse_mode: 'Markdown',
      ...keyboard
    });
    return;
  }
  
  // Help
  if (data === 'main_help') {
    const helpText = `${EMOJIS.help} *Help Center* ${EMOJIS.help}\n\n${EMOJIS.success} */start* - Show main menu\n${EMOJIS.success} */key <key>* - Redeem your access key\n${EMOJIS.success} Use the generate button to get accounts\n\n${EMOJIS.success} *How to use:*\n1. Get an access key from admin\n2. Redeem it using /key command\n3. Use the generate button to get accounts\n\n${EMOJIS.error} *Important:*\n• Don't share your key with others\n• Report any issues to admin`;
    
    const keyboard = {
      reply_markup: {
        inline_keyboard: [
          [{ text: `${EMOJIS.back} Main Menu`, callback_data: 'main_menu' }]
        ]
      }
    };
    
    bot.editMessageText(helpText, {
      chat_id: chatId,
      message_id: msg.message_id,
      parse_mode: 'Markdown',
      ...keyboard
    });
    return;
  }
  
  // Redeem key instructions
  if (data === 'main_redeem') {
    const redeemText = `${EMOJIS.key} *Redeem Key*\n\nUse the command:\n\`/key YOUR_KEY_HERE\`\n\nExample:\n\`/key TOLLIPOP-ABC123\`\n\nGet keys from the admin.`;
    
    const keyboard = {
      reply_markup: {
        inline_keyboard: [
          [{ text: `${EMOJIS.back} Main Menu`, callback_data: 'main_menu' }]
        ]
      }
    };
    
    bot.editMessageText(redeemText, {
      chat_id: chatId,
      message_id: msg.message_id,
      parse_mode: 'Markdown',
      ...keyboard
    });
    return;
  }
  
  // Admin panel
  if (data === 'main_admin') {
    if (!isAdmin(userId)) {
      return bot.editMessageText(`${EMOJIS.error} You are not authorized to access this panel!`, {
        chat_id: chatId,
        message_id: msg.message_id
      });
    }
    
    const totalUsers = Object.keys(userKeys).length;
    const availableKeys = Object.keys(keysDB).length;
    
    const keyboard = {
      reply_markup: {
        inline_keyboard: [
          [{ text: `${EMOJIS.key} Generate Key`, callback_data: 'admin_genkey' }],
          [{ text: `${EMOJIS.success} Stats`, callback_data: 'admin_stats' }],
          [{ text: `${EMOJIS.back} Main Menu`, callback_data: 'main_menu' }]
        ]
      }
    };
    
    bot.editMessageText(`${EMOJIS.admin} *ADMIN PANEL* ${EMOJIS.admin}\n\n${EMOJIS.success} Total Users: ${totalUsers}\n${EMOJIS.key} Available Keys: ${availableKeys}\n\nSelect an option to manage the bot:`, {
      chat_id: chatId,
      message_id: msg.message_id,
      parse_mode: 'Markdown',
      ...keyboard
    });
    return;
  }
  
  // Admin generate key
  if (data === 'admin_genkey') {
    if (!isAdmin(userId)) {
      return;
    }
    
    const newKey = generateRandomKey();
    keysDB[newKey] = true;
    
    bot.editMessageText(`${EMOJIS.success} *New Key Generated!*\n\n${EMOJIS.key} Key: \`${newKey}\`\n\nShare this key with your users!`, {
      chat_id: chatId,
      message_id: msg.message_id,
      parse_mode: 'Markdown'
    });
    return;
  }
  
  // Admin stats
  if (data === 'admin_stats') {
    if (!isAdmin(userId)) {
      return;
    }
    
    const totalUsers = Object.keys(userKeys).length;
    const availableKeys = Object.keys(keysDB).length;
    const bannedCount = bannedUsers.size;
    
    const keyboard = {
      reply_markup: {
        inline_keyboard: [
          [{ text: `${EMOJIS.back} Admin Panel`, callback_data: 'main_admin' }]
        ]
      }
    };
    
    bot.editMessageText(`${EMOJIS.success} *Admin Statistics*\n\n${EMOJIS.success} Total Users: ${totalUsers}\n${EMOJIS.key} Available Keys: ${availableKeys}\n${EMOJIS.error} Banned Users: ${bannedCount}\n${EMOJIS.success} Platforms: ${Object.keys(accountsDB).length}`, {
      chat_id: chatId,
      message_id: msg.message_id,
      parse_mode: 'Markdown',
      ...keyboard
    });
    return;
  }
});

// === CREATE SOME DEMO KEYS ===
keysDB['TOLLIPOP-DEMO123'] = true;
keysDB['TOLLIPOP-TEST456'] = true;

// === EXPRESS SERVER FOR RENDER ===
const app = express();
app.get('/', (req, res) => {
  res.send('🤖 TOLLIPOP BOT IS RUNNING!');
});

app.listen(PORT, () => {
  console.log(`🚀 Bot server running on port ${PORT}`);
  console.log('🤖 TOLLIPOP BOT STARTED!');
  console.log('✅ Bot is running and waiting for messages...');
});
