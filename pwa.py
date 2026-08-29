"""Ativa o app como PWA instalável: injeta o link do manifesto, o ícone para
iOS e registra o service worker no <head> real da página.

O componente do Streamlit roda dentro de um iframe do mesmo site, então o
script consegue alcançar `window.parent.document` para editar o <head> de
verdade (o Streamlit não expõe uma forma direta de fazer isso).
"""
import streamlit.components.v1 as components

_SCRIPT = """
<script>
(function () {
  try {
    var doc = window.parent.document;

    function addOnce(selector, build) {
      if (!doc.querySelector(selector)) {
        doc.head.appendChild(build());
      }
    }

    addOnce('link[rel="manifest"]', function () {
      var l = doc.createElement('link');
      l.rel = 'manifest';
      l.href = '/app/static/manifest.json';
      return l;
    });

    addOnce('meta[name="theme-color"]', function () {
      var m = doc.createElement('meta');
      m.name = 'theme-color';
      m.content = '#8c2f52';
      return m;
    });

    addOnce('link[rel="apple-touch-icon"]', function () {
      var l = doc.createElement('link');
      l.rel = 'apple-touch-icon';
      l.href = '/app/static/apple-touch-icon.png';
      return l;
    });

    addOnce('meta[name="apple-mobile-web-app-capable"]', function () {
      var m = doc.createElement('meta');
      m.name = 'apple-mobile-web-app-capable';
      m.content = 'yes';
      return m;
    });

    addOnce('meta[name="apple-mobile-web-app-title"]', function () {
      var m = doc.createElement('meta');
      m.name = 'apple-mobile-web-app-title';
      m.content = 'AR Confeitaria';
      return m;
    });

    if ('serviceWorker' in navigator) {
      navigator.serviceWorker.register('/app/static/sw.js').catch(function () {});
    }
  } catch (e) {
    // Se por algum motivo o parent nao for acessivel, o app segue funcionando
    // normalmente -- só sem a opção de "instalar".
  }
})();
</script>
"""


def enable_pwa() -> None:
    components.html(_SCRIPT, height=0, width=0)
