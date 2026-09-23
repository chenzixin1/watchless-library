/* ==========================================================================
   AI 实践库 · 固定脚本
   数据来源：data/catalog.js、data/lesson-<id>.js（由 tools/ingest.py 生成）
   新增课程时不需要修改本文件。
   ========================================================================== */

(function () {
  'use strict';

  var K_PROGRESS = 'learning-site:progress:';
  var K_LAST = 'learning-site:last';
  var K_SPLIT = 'learning-site:split';
  var reduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  /* ---------------- utils ---------------- */

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
    page.appendChild(el('span', 'eyebrow', 'AI 实践库'));
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
    brand.appendChild(el('span', 'brand-mark', 'AI'));
    brand.appendChild(el('span', 'brand-name', (window.__SITE__ && window.__SITE__.brand) || 'AI 实践库'));
    bar.appendChild(brand);

    var nav = el('nav', 'global-nav');
    var bArchive = el('button', activePage === 'archive' ? 'active' : null, '分享档案');
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
      input.placeholder = '搜索分享';
      input.value = query || '';
      input.setAttribute('aria-label', '顶部搜索分享');
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
    tools.appendChild(el('span', 'header-note', '技术运营部'));
    bar.appendChild(tools);
    document.body.insertBefore(bar, document.body.firstChild);
  }

  /* ==================== archive page ==================== */

  function initArchive() {
    var mount = $('#app');
    var params = new URLSearchParams(location.search);
    var query = params.get('q') || '';
    var month = params.get('m') || '';
    var sortOrder = read('learning-site:sort', 'newest');
    var catalog = [];

    loadScript('data/catalog.js', '__CATALOG__').then(function (data) {
      catalog = (data && data.lessons) || [];
      window.__SITE__ = (data && data.site) || {};
      document.title = (window.__SITE__.brand || 'AI 实践库') + ' · 分享档案';
      renderTopbar('archive', query);
      render();
    }).catch(function (err) {
      statePage(mount, '还没有可用的分享',
        '用 tools/ingest.py 导入第一场分享，然后刷新本页。', '重新加载', location.pathname);
      console.error(err);
    });

    function filtered() {
      var q = query.trim().toLowerCase();
      var list = catalog.filter(function (x) {
        if (month && x.month !== month) return false;
        if (!q) return true;
        return [x.title, x.speaker, x.source, (x.tags || []).join(' ')]
          .join(' ').toLowerCase().indexOf(q) >= 0;
      });
      list.sort(function (a, b) {
        var d = String(b.date || '').localeCompare(String(a.date || ''));
        if (d !== 0) return sortOrder === 'newest' ? d : -d;
        return (a.order || 0) - (b.order || 0);
      });
      return list;
    }

    function render() {
      mount.innerHTML = '';
      var page = el('div', 'archive');
      page.appendChild(renderIntro());
      page.appendChild(renderMonthNav());
      page.appendChild(renderBody());
      mount.appendChild(page);
    }

    function renderIntro() {
      var intro = el('section', 'archive-intro');
      var left = el('div');
      left.appendChild(el('span', 'eyebrow', 'TECH OPS · LEARNING ARCHIVE'));
      left.appendChild(el('h1', null, '分享档案'));
      left.appendChild(el('p', null, '视频与图文笔记 · 点开任意一场，边看边读'));
      intro.appendChild(left);

      var totalSeconds = catalog.reduce(function (s, x) { return s + (Number(x.duration) || 0); }, 0);
      var months = {};
      catalog.forEach(function (x) { months[x.month] = 1; });
      var stats = el('div', 'archive-stats');
      [[catalog.length, '场分享'], [Object.keys(months).length, '个月份'],
       formatArchiveLength(totalSeconds)].forEach(function (pair) {
        var d = el('div');
        var s = el('strong', null, String(pair[0]));
        d.appendChild(s);
        d.appendChild(el('span', null, pair[1]));
        stats.appendChild(d);
      });
      intro.appendChild(stats);
      return intro;
    }

  function monthLabel_PLACEHOLDER() { return ''; }
