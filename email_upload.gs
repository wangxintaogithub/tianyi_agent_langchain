/**
 * Gmail → TianYi Upload API
 *
 * 扫描未读邮件，将邮件正文 + 附件上传到后端 API。
 * 定时触发器由用户在 GAS 编辑器里手动添加（指向 main 函数）。
 *
 * 部署：
 *   1. https://script.google.com 新建项目
 *   2. 粘贴本代码 → 保存
 *   3. 编辑器左侧 ⏰ 触发器 → 添加触发器 → 选择 main / 时间驱动 / 任意频率
 *   4. 首次运行会弹 OAuth 授权（需授予 Gmail + 外部 URL 权限）
 */

// ============== 配置 ==============
const CONFIG = {
  apiUrl:       'https://xiaoyuetech.online/api/upload',
  apiToken:     '',
  uploadToCos:  true,
  sendToWechat: true,
  searchQuery:  'is:unread has:attachment',   // 只扫描有附件的未读邮件
};
// ==================================


// ============== 主流程 ==============

function main() {
  Logger.log('=== main 开始 ===');
  const threads = GmailApp.search(CONFIG.searchQuery);
  Logger.log('命中未读会话：%s', threads.length);

  if (threads.length === 0) {
    Logger.log('无新邮件，结束 ===');
    return;
  }

  let uploaded = 0, skipped = 0;
  threads.forEach(thread => {
    thread.getMessages().forEach(msg => {
      if (!msg.isUnread()) return;
      try {
        if (uploadMessage(msg)) uploaded++;
        else skipped++;
        msg.markRead();
      } catch (e) {
        Logger.log('✘ 处理失败: [%s] %s', msg.getSubject(), e.message);
      }
    });
  });

  Logger.log('=== main 结束：上传 %s / 跳过 %s ===', uploaded, skipped);
}


/** 上传单封邮件。返回 true=已上传，false=跳过 */
function uploadMessage(msg) {
  const attachments = msg.getAttachments();
  if (attachments.length === 0) {
    Logger.log('⏭ 无附件，跳过: %s', msg.getSubject());
    return false;
  }

  Logger.log('⇪ 上传: [%s] %s (附件 %s 个)',
             msg.getFrom(), msg.getSubject(), attachments.length);

  // 正文 → Blob
  const bodyBlob = Utilities.newBlob(
    buildEmailText(msg),
    'text/plain;charset=utf-8',
    `email-${msg.getId()}.txt`
  );

  // 所有待上传文件
  const files = [bodyBlob, ...attachments.map(a => a.copyBlob())];
  files.forEach(b => {
    Logger.log('   · %s (%s KB)', b.getName(), (b.getBytes().length / 1024).toFixed(1));
  });

  const payload = buildMultipart(files);
  Logger.log('请求体总大小: %s B', payload.getBytes().length);

  const res = UrlFetchApp.fetch(CONFIG.apiUrl, {
    method: 'POST',
    payload,
    headers: { Authorization: `Bearer ${CONFIG.apiToken}` },
    muteHttpExceptions: true,
  });

  const code = res.getResponseCode();
  Logger.log('⬇ 响应 %s: %s', code, res.getContentText().slice(0, 500));

  if (code < 200 || code >= 300) {
    throw new Error(`HTTP ${code}`);
  }
  Logger.log('✔ 上传成功');
  return true;
}


// ============== 工具：Multipart 构造器 ==============

/**
 * 手动拼装 multipart/form-data。
 *
 * GAS 的 UrlFetchApp 在处理同名字段的多个 Blob 时编码不稳定，
 * 所以我们直接拼字节。FastAPI/Python 端可以正常解析。
 */
function buildMultipart(files) {
  const boundary = `----TianYi_${Date.now()}_${Math.random().toString(36).slice(2, 12)}`;
  const chunks = [];

  // 文本字段
  chunks.push(asBlob(makeField('upload_to_cos',  CONFIG.uploadToCos  ? 'true' : 'false', boundary)));
  chunks.push(asBlob(makeField('send_to_wechat', CONFIG.sendToWechat ? 'true' : 'false', boundary)));

  // 文件字段（同名 files）
  files.forEach(file => {
    chunks.push(asBlob(
      `--${boundary}\r\n` +
      `Content-Disposition: form-data; name="files"; filename="${file.getName()}"\r\n` +
      `Content-Type: ${file.getContentType()}\r\n\r\n`
    ));
    chunks.push(file);                          // 原始字节
    chunks.push(asBlob('\r\n'));
  });

  chunks.push(asBlob(`--${boundary}--\r\n`));

  // 合并字节数组
  const out = [];
  chunks.forEach(c => {
    const bytes = c.getBytes();
    for (let i = 0; i < bytes.length; i++) out.push(bytes[i]);
  });

  return Utilities.newBlob(out, `multipart/form-data; boundary=${boundary}`);
}

function makeField(name, value, boundary) {
  return `--${boundary}\r\n` +
         `Content-Disposition: form-data; name="${name}"\r\n\r\n` +
         `${value}\r\n`;
}

function asBlob(text) {
  return Utilities.newBlob(text, 'text/plain;charset=utf-8');
}


// ============== 工具：构建邮件正文文本 ==============

function buildEmailText(msg) {
  return [
    '========================================',
    '  邮件转发 - TianYi Upload API',
    '========================================',
    '',
    `From:    ${msg.getFrom() || ''}`,
    `To:      ${msg.getTo()   || ''}`,
    `Date:    ${msg.getDate().toISOString()}`,
    `Subject: ${msg.getSubject() || '(无主题)'}`,
    '',
    '----------------------------------------',
    '  邮件正文',
    '----------------------------------------',
    '',
    msg.getPlainBody() || '(无正文内容)',
    '',
    '========================================',
  ].join('\n');
}


// ============== 手动调试 ==============

function testNow() {
  Logger.log('[testNow] 手动触发 main()');
  main();
}

function testSingle(id) {
  // 调试用：传入邮件 message id 上传指定邮件
  const msg = GmailApp.getMessageById(id);
  uploadMessage(msg);
}