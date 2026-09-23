/* ==========================================================================
   Watchless 知识库 · 固定脚本
   数据来源：data/catalog.js、data/lesson-<id>.js（由 tools/ingest.py 生成）
   新增学习视频时不需要修改本文件。
   ========================================================================== */

(function () {
  'use strict';

  var K_PROGRESS = 'learning-site:progress:';
  var K_LAST = 'learning-site:last';
  var K_SPLIT = 'learning-site:split';
  var reduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  function $(sel, root) { return (root || document).querySelector(sel); }
  function $$(sel, root) { return Array.prototype.slice.call((root || document).querySelectorAll(sel)); }
  function el(tag, cls, text) {
    var n = document.createElement(tag);
    if (cls) n.className = cls;
    if (text != null) n.textContent = text;
    return n;
  }
  function pad(n) { return String(n).padStart(2, '0'); }
  function format(t) {
    t = Math.max(0, Math.floor(Number(t) || 0));
    var h = Math.floor(t / 3600);
    return (h ? h + ':' : '') + pad(Math.floor(t / 60) % 60) + ':' + pad(t % 60);
  }
  function formatArchiveLength(totalSeconds) {
    var seconds = Math.max(0, Number(totalSeconds) || 0);
    if (seconds < 3600) {
      return [Math.max(1, Math.round(seconds / 60)), '分钟内容'];
    }
    var hours = Math.round(seconds / 360) / 10;
    return [Number.isInteger(hours) ? String(hours) : hours.toFixed(1), '小时内容'];
  }
  function monthLabel(key) {
    var m = /^(\d{4})-(\d{2})$/.exec(key || '');
    return m ? m[1] + ' 年 ' + Number(m[2]) + ' 月' : (key || '未归类');
  }
  function monthBadge(key) {
    var m = /^(\d{4})-(\d{2})$/.exec(key || '');
    return m ? m[1].slice(2) + '.' + m[2] : '--';
  }
  function read(key, fallback) {
    try { var v = JSON.parse(localStorage.getItem(key)); return v == null ? fallback : v; }
    catch (e) { return fallback; }
  }
  function write(key, value) {
    try { localStorage.setItem(key, JSON.stringify(value)); } catch (e) {}
  }
  function loadScript(src, globalName) {
    return new Promise(function (resolve, reject) {
      var s = document.createElement('script');
      s.src = src;
      s.onload = function () {
        var data = window[globalName];
        delete window[globalName];
        data ? resolve(data) : reject(new Error('数据格式异常：' + src));
      };
      s.onerror = function () { reject(new Error('无法加载 ' + src)); };
      document.head.appendChild(s);
    });
  }
  function statePage(mount, title, message, actionText, actionHref) {
    mount.innerHTML = '';
    var page = el('main', 'state-page');
    page.appendChild(el('span', 'eyebrow', 'Watchless 知识库'));
    page.appendChild(el('h1', null, title));
    if (message) page.appendChild(el('p', null, message));
    if (actionText) {
      var a = el('a', 'primary-link', actionText);
      a.href = actionHref || './index.html';
      page.appendChild(a);
    }
    mount.appendChild(page);
  }
  function renderTopbar(activePage, query) {
    var bar = el('header', 'topbar');
    var brand = el('a', 'brand');
    brand.href = './index.html';
    brand.appendChild(el('span', 'brand-mark', 'W'));
    brand.appendChild(el('span', 'brand-name', (window.__SITE__ && window.__SITE__.brand) || 'Watchless 知识库'));
    bar.appendChild(brand);
    var nav = el('nav', 'global-nav');
    var bArchive = el('button', activePage === 'archive' ? 'active' : null, '学习视频');
    bArchive.addEventListener('click', function () { location.href = './index.html'; });
    nav.appendChild(bArchive);
    if (activePage === 'lesson') {
      var bNow = el('button', 'active', '当前阅读');
      nav.appendChild(bNow);
    }
    bar.appendChild(nav);
    var tools = el('div', 'header-tools');
    if (activePage === 'archive') {
      var form = el('form', 'header-search');
      var input = el('input');
      input.type = 'search';
      input.placeholder = '搜索视频';
      input.value = query || '';
      input.setAttribute('aria-label', '搜索视频');
      form.appendChild(input);
      var btn = el('button', null, '\u2315');
      btn.type = 'submit';
      btn.setAttribute('aria-label', '搜索');
      form.appendChild(btn);
      form.addEventListener('submit', function (e) {
        e.preventDefault();
        location.hash = '';
        var val = input.value.trim();
        location.search = val ? '?q=' + encodeURIComponent(val) : '';
      });
      tools.appendChild(form);
    }
    bar.appendChild(tools);
    document.body.insertBefore(bar, document.body.firstChild);
  }
  document.addEventListener('DOMContentLoaded', function () {
    var page = document.body.getAttribute('data-page');
    if (page === 'archive') initArchive();
    else if (page === 'lesson') initLesson();
  });
})();
