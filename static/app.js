const form = document.querySelector("#builderForm");
const yamlOutput = document.querySelector("#yamlOutput");
const runOutput = document.querySelector("#runOutput");
const statusEl = document.querySelector("#status");
const importFileName = document.querySelector("#importFileName");

function apiPath(path) {
  const current = new URL(window.location.href);
  if (current.protocol === "file:") {
    return path;
  }
  const basePath = current.pathname.endsWith("/") ? current.pathname : current.pathname.replace(/[^/]*$/, "");
  return new URL(path.replace(/^\//, ""), `${current.origin}${basePath}`).pathname;
}

const endpoints = {
  configs: apiPath("api/configs"),
  configBase: apiPath("api/config/__NAME__"),
  parse: apiPath("api/parse"),
  generate: apiPath("api/generate"),
  save: apiPath("api/save"),
  run: apiPath("api/run"),
};

function configUrl(name) {
  return endpoints.configBase.replace("__NAME__", encodeURIComponent(name));
}

async function readJson(response) {
  const contentType = response.headers.get("content-type") || "";
  if (!contentType.includes("application/json")) {
    const text = await response.text();
    throw new Error(`接口返回 HTML 而不是 JSON。请通过 Flask 地址打开页面，例如 http://127.0.0.1:5000。返回片段：${text.slice(0, 80)}`);
  }
  return response.json();
}

async function loadConfigList() {
  const select = document.querySelector("#configSelect");
  const hint = document.querySelector("#configListHint");
  if (!select) {
    return;
  }
  try {
    const response = await fetch(endpoints.configs);
    const data = await readJson(response);
    if (!data.ok) {
      throw new Error(data.error || "配置列表读取失败");
    }
    if (Array.isArray(data.configs) && data.configs.length) {
      select.innerHTML = "";
      for (const name of data.configs) {
        const option = document.createElement("option");
        option.value = name;
        option.textContent = name;
        select.appendChild(option);
      }
    }
    if (!data.configs.length && !select.options.length) {
      const option = document.createElement("option");
      option.value = "";
      option.textContent = "暂无配置";
      select.appendChild(option);
    }
    if (hint) {
      hint.textContent = `已从 configs 目录加载 ${data.configs.length} 个配置`;
      hint.classList.remove("warn");
    }
  } catch (error) {
    select.innerHTML = "<option value=\"\">后端 API 未连接</option>";
    if (hint) {
      hint.textContent = `配置列表读取失败：${error.message}`;
      hint.classList.add("warn");
    }
  }
}

function formPayload() {
  const data = new FormData(form);
  const payload = {};
  for (const [key, value] of data.entries()) {
    payload[key] = value;
  }
  for (const input of form.querySelectorAll('input[type="checkbox"]')) {
    payload[input.name] = input.checked;
  }
  payload.config_name = data.get("config_name") || "ui_generated.yaml";
  return payload;
}

function setField(name, value) {
  const field = form.querySelector(`[name="${name}"]`);
  if (!field || value === undefined || value === null) {
    return;
  }
  if (field.type === "checkbox") {
    field.checked = Boolean(value);
    return;
  }
  if (field.tagName === "SELECT" && !Array.from(field.options).some((option) => option.value === String(value))) {
    const option = document.createElement("option");
    option.value = value;
    option.textContent = value;
    field.appendChild(option);
  }
  field.value = Array.isArray(value) ? value.join("\n") : value;
}

function formatFields(fields) {
  if (!fields || typeof fields !== "object") {
    return "";
  }
  return Object.entries(fields)
    .map(([name, rule]) => {
      if (typeof rule === "string") {
        return `${name}|${rule}`;
      }
      const parts = [
        name,
        rule.selector || "",
        rule.mode || "",
        rule.many ? "true" : "",
        rule.transform || "",
      ];
      while (parts.length > 2 && !parts[parts.length - 1]) {
        parts.pop();
      }
      return parts.join("|");
    })
    .join("\n");
}

function formatApiFields(fields) {
  if (!fields || typeof fields !== "object") {
    return "";
  }
  return Object.entries(fields).map(([name, path]) => `${name}|${path}`).join("\n");
}

function resourceFields(resources, type) {
  const resource = (resources || []).find((item) => item.type === type);
  return resource && Array.isArray(resource.url_fields) ? resource.url_fields.join(",") : "";
}

function applyConfigToForm(config, filename) {
  setField("config_name", filename || "ui_generated.yaml");
  setField("task_name", config.task?.name);
  setField("purpose", config.task?.purpose);
  setField("description", config.task?.description);
  setField("site_name", config.target?.site_name);
  setField("base_url", config.target?.base_url);
  setField("entry_urls", config.target?.entry_urls);
  setField("allowed_domains", config.target?.allowed_domains);

  setField("request_type", config.request?.type);
  setField("method", config.request?.method);
  setField("encoding", config.request?.encoding);
  setField("user_agent", config.request?.headers?.["User-Agent"]);
  setField("authorization", config.request?.headers?.Authorization);
  setField("referer", config.request?.headers?.Referer);

  setField("browser_enabled", config.browser?.enabled);
  setField("browser_engine", config.browser?.engine);
  setField("headless", config.browser?.headless);
  setField("wait_until", config.browser?.wait_until);
  setField("wait_selector", config.browser?.wait_selector);
  const scrollAction = (config.browser?.actions || []).find((action) => action.type === "scroll");
  const waitAction = (config.browser?.actions || []).find((action) => action.type === "wait");
  setField("scroll_enabled", Boolean(scrollAction));
  setField("scroll_times", scrollAction?.times);
  setField("scroll_pause", scrollAction?.pause);
  setField("wait_seconds", waitAction?.seconds);

  setField("pagination_type", config.pagination?.enabled ? config.pagination?.type : "none");
  setField("start_page", config.pagination?.start_page);
  setField("end_page", config.pagination?.end_page);
  setField("page_param", config.pagination?.page_param);
  setField("max_pages", config.pagination?.max_pages);
  setField("cursor_param", config.pagination?.cursor_param);
  setField("url_template", config.pagination?.url_template);
  setField("next_page_selector", config.pagination?.next_page_selector);
  setField("next_cursor_path", config.pagination?.next_cursor_path);

  setField("item_selector", config.list?.item_selector);
  setField("fields", formatFields(config.list?.fields));
  setField("api_fields", formatApiFields(config.api?.fields));
  setField("api_data_path", config.api?.data_path);
  setField("detail_enabled", config.detail?.enabled);
  setField("detail_url_field", config.detail?.url_field);
  setField("detail_fields", formatFields(config.detail?.fields));

  setField("media_enabled", config.media?.enabled);
  setField("parse_attachments", config.media?.parse_attachments);
  setField("media_output_dir", config.media?.output_dir);
  setField("parse_max_chars", config.media?.parse_config?.max_chars);
  setField("image_fields", resourceFields(config.media?.resources, "image"));
  setField("audio_fields", resourceFields(config.media?.resources, "audio"));
  setField("video_fields", resourceFields(config.media?.resources, "video"));
  setField("subtitle_fields", resourceFields(config.media?.resources, "subtitle"));
  setField("attachment_fields", resourceFields(config.media?.resources, "attachment"));

  setField("storage_type", config.storage?.type);
  setField("output_path", config.storage?.path);
  setField("table", config.storage?.table);
  setField("dedupe_enabled", config.dedupe?.enabled);
  setField("dedupe_type", config.dedupe?.type);
  setField("dedupe_fields", (config.dedupe?.key_fields || []).join(","));
  setField("resume_enabled", config.resume?.enabled);
  setField("retry_failed_first", config.resume?.retry_failed_first);
  setField("logging_enabled", config.logging?.enabled);
  setField("retry_times", config.retry?.times);
  setField("retry_backoff", config.retry?.backoff);
  setField("delay_min", config.rate_limit?.delay_min);
  setField("delay_max", config.rate_limit?.delay_max);
}

async function postJson(url, payload) {
  const response = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  const data = await readJson(response);
  if (!response.ok || !data.ok) {
    throw new Error(data.error || `Request failed: ${response.status}`);
  }
  return data;
}

async function generateYaml() {
  statusEl.textContent = "生成中";
  const data = await postJson(endpoints.generate, formPayload());
  yamlOutput.value = data.yaml;
  statusEl.textContent = "已生成";
}

async function saveYaml() {
  if (!yamlOutput.value.trim()) {
    await generateYaml();
  }
  const payload = formPayload();
  payload.name = payload.config_name;
  payload.yaml = yamlOutput.value;
  const data = await postJson(endpoints.save, payload);
  statusEl.textContent = `已保存 ${data.path}`;
}

async function runTask() {
  if (!yamlOutput.value.trim()) {
    await generateYaml();
  }
  runOutput.textContent = "任务运行中，请稍等...";
  statusEl.textContent = "运行中";
  const payload = formPayload();
  payload.name = payload.config_name;
  payload.yaml = yamlOutput.value;
  try {
    const data = await postJson(endpoints.run, payload);
    runOutput.textContent = `${data.stdout || ""}${data.stderr ? "\n[stderr]\n" + data.stderr : ""}`.trim() || "任务已完成，无输出。";
    statusEl.textContent = data.ok ? "运行完成" : "运行失败";
  } catch (error) {
    runOutput.textContent = error.message;
    statusEl.textContent = "运行失败";
  }
}

async function loadSelectedConfig() {
  const name = document.querySelector("#configSelect").value;
  if (!name) {
    statusEl.textContent = "未选择配置";
    return;
  }
  const response = await fetch(configUrl(name));
  const data = await readJson(response);
  if (!data.ok) {
    throw new Error(data.error || "读取失败");
  }
  yamlOutput.value = data.yaml;
  applyConfigToForm(data.config || {}, name);
  statusEl.textContent = `已读取 ${name}`;
}

async function importLocalConfig(file) {
  if (!file) {
    return;
  }
  if (importFileName) {
    importFileName.textContent = file.name;
  }
  const yaml = await file.text();
  const data = await postJson(endpoints.parse, { yaml });
  yamlOutput.value = yaml;
  applyConfigToForm(data.config || {}, file.name);
  statusEl.textContent = `已导入 ${file.name}`;
}

document.querySelector("#generateBtn").addEventListener("click", () => {
  generateYaml().catch((error) => {
    statusEl.textContent = "生成失败";
    runOutput.textContent = error.message;
  });
});

document.querySelector("#saveBtn").addEventListener("click", () => {
  saveYaml().catch((error) => {
    statusEl.textContent = "保存失败";
    runOutput.textContent = error.message;
  });
});

document.querySelector("#runBtn").addEventListener("click", runTask);

document.querySelector("#loadBtn").addEventListener("click", () => {
  loadSelectedConfig().catch((error) => {
    statusEl.textContent = "读取失败";
    runOutput.textContent = error.message;
  });
});

document.querySelector("#importFile").addEventListener("change", (event) => {
  const file = event.target.files[0];
  importLocalConfig(file).catch((error) => {
    statusEl.textContent = "导入失败";
    if (importFileName && file) {
      importFileName.textContent = `导入失败：${file.name}`;
    }
    runOutput.textContent = error.message;
  });
  event.target.value = "";
});

generateYaml().catch(() => {
  statusEl.textContent = "等待输入";
});

loadConfigList();
