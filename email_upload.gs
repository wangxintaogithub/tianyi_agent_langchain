// ============================================================
// Gmail → TianYi Upload API 自动转发脚本
// 每 5 分钟检查未读邮件，有附件的自动上传到后端 API
// ============================================================
// 部署方式：
//   1. 在 https://script.google.com 创建新项目
//   2. 粘贴此代码
//   3. 修改下方配置区的 API_ENDPOINT 和 API_KEY
//   4. 运行 setupTrigger() 初始化定时触发器
// ============================================================

// ========== 配置区（请修改） ==========
const API_ENDPOINT = 'https://www.xiaoyuetech.online/api/upload';
const API_KEY = '你的 API_UPLOAD_KEY';  // 与服务端 API_UPLOAD_KEY 一致
const UPLOAD_TO_COS = true;             // 是否上传到腾讯云 COS
const SEND_TO_WECHAT = true;            // 是否发送企业微信通知
// ======================================


// ========== 设置定时触发器（每 5 分钟） ==========
function setupTrigger() {
  // 清除已有的 main 触发器，避免重复
  const triggers = ScriptApp.getProjectTriggers();
  triggers.forEach(t => {
    if (t.getHandlerFunction() === 'main') {
      ScriptApp.deleteTrigger(t);
      console.log('已删除旧触发器');
    }
  });

  // 创建每 5 分钟执行一次的触发器
  ScriptApp.newTrigger('main')
    .timeBased()
    .everyMinutes(5)
    .create();

  console.log('✅ 定时触发器已创建，每 5 分钟执行一次 main()');
}


// ========== 删除定时触发器 ==========
function removeTrigger() {
  const triggers = ScriptApp.getProjectTriggers();
  triggers.forEach(t => {
    if (t.getHandlerFunction() === 'main') {
      ScriptApp.deleteTrigger(t);
    }
  });
  console.log('🗑️ 已删除所有 main 触发器');
}


// ========== 主函数（每 5 分钟触发） ==========
function main() {
  console.log('🔄 [开始] 检查新邮件...');

  const threads = GmailApp.search('is:unread');
  console.log(`📬 未读会话数: ${threads.length}`);

  if (threads.length === 0) {
    console.log('✅ [结束] 没有新邮件');
    return;
  }

  let processedCount = 0;
  let uploadedCount = 0;

  threads.forEach(thread => {
    const messages = thread.getMessages();
    messages.forEach(message => {
      if (!message.isUnread()) return;

      const subject = message.getSubject() || '(无主题)';
      console.log(`📧 处理邮件: ${subject}`);

      const attachments = message.getAttachments();
      if (attachments.length > 0) {
        console.log(`📎 发现 ${attachments.length} 个附件，调用 Upload API`);
        uploadEmailToAPI(message, attachments);
        uploadedCount++;
      } else {
        console.log(`⏭️ 无附件，跳过: ${subject}`);
      }

      message.markRead();  // 标记已读，避免重复处理
      processedCount++;
    });
  });

  console.log(`✅ [结束] 处理 ${processedCount} 封，上传 ${uploadedCount} 封`);
}


// ========== 调用 Upload API（multipart/form-data） ==========
function uploadEmailToAPI(message, attachments) {
  // 构建邮件正文内容（作为第一个文件发送）
  const emailBody = buildEmailBody(message);
  const emailBlob = Utilities.newBlob(
    emailBody,
    'text/plain;charset=utf-8',
    `email-${message.getId()}.txt`
  );

  // 构建 multipart form-data payload
  // files 字段传入 Blob 数组，UrlFetchApp 会自动编码为 multipart
  const formData = {
    files: [emailBlob],
    upload_to_cos: UPLOAD_TO_COS ? 'true' : 'false',
    send_to_wechat: SEND_TO_WECHAT ? 'true' : 'false',
  };

  // 逐个添加附件 Blob
  attachments.forEach(attachment => {
    formData.files.push(attachment);
  });

  const options = {
    method: 'post',
    payload: formData,
    headers: {
      Authorization: 'Bearer ' + API_KEY,
    },
    muteHttpExceptions: true,
  };

  try {
    const response = UrlFetchApp.fetch(API_ENDPOINT, options);
    const respCode = response.getResponseCode();
    const respText = response.getContentText();

    if (respCode >= 200 && respCode < 300) {
      console.log(`✅ 上传成功: ${message.getSubject()} (${respCode})`);
    } else {
      console.error(`❌ 上传失败: ${message.getSubject()} (${respCode}): ${respText}`);
    }
  } catch (e) {
    console.error(`❌ 上传异常: ${message.getSubject()}, 错误: ${e.toString()}`);
  }
}


// ========== 构建邮件正文文本 ==========
function buildEmailBody(message) {
  const lines = [
    '========================================',
    '  邮件转发 - TianYi Upload API',
    '========================================',
    '',
    `From:    ${message.getFrom()}`,
    `To:      ${message.getTo() || ''}`,
    `Date:    ${message.getDate().toISOString()}`,
    `Subject: ${message.getSubject() || '(无主题)'}`,
    '',
    '----------------------------------------',
    '  邮件正文',
    '----------------------------------------',
    '',
    message.getPlainBody() || '(无正文内容)',
    '',
    '========================================',
  ];
  return lines.join('\n');
}


// ========== 手动测试（在编辑器里运行） ==========
function testNow() {
  console.log('🧪 手动执行 main()...');
  main();
}
