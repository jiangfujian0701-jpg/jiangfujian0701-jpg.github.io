package nyc.npsa.app;

import android.annotation.SuppressLint;
import android.app.Activity;
import android.content.Intent;
import android.graphics.Bitmap;
import android.net.Uri;
import android.os.Bundle;
import android.view.KeyEvent;
import android.view.View;
import android.webkit.WebResourceError;
import android.webkit.WebResourceRequest;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.webkit.WebViewClient;

public class MainActivity extends Activity {
    private static final String HOME = "https://jiangfujian0701-jpg.github.io/";
    private WebView web;

    @SuppressLint("SetJavaScriptEnabled")
    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);

        web = new WebView(this);
        web.setBackgroundColor(0xFF000000);
        WebSettings s = web.getSettings();
        s.setJavaScriptEnabled(true);
        s.setDomStorageEnabled(true);
        s.setDatabaseEnabled(true);
        s.setCacheMode(WebSettings.LOAD_DEFAULT);
        s.setMediaPlaybackRequiresUserGesture(true);
        s.setSupportZoom(false);
        s.setBuiltInZoomControls(false);
        s.setAllowFileAccess(false);
        s.setAllowContentAccess(false);
        s.setMixedContentMode(WebSettings.MIXED_CONTENT_NEVER_ALLOW);
        s.setUserAgentString(s.getUserAgentString() + " NPSAApp/1.0");
        web.setOverScrollMode(View.OVER_SCROLL_NEVER);

        web.setWebViewClient(new WebViewClient() {
            @Override
            public boolean shouldOverrideUrlLoading(WebView v, WebResourceRequest req) {
                Uri u = req.getUrl();
                String host = u.getHost() == null ? "" : u.getHost();
                if (host.endsWith("jiangfujian0701-jpg.github.io")) return false;
                try { startActivity(new Intent(Intent.ACTION_VIEW, u)); } catch (Exception ignored) {}
                return true;
            }
            @Override
            public void onPageStarted(WebView v, String url, Bitmap favicon) { v.setVisibility(View.INVISIBLE); }
            @Override
            public void onPageFinished(WebView v, String url) { v.setVisibility(View.VISIBLE); }
            @Override
            public void onReceivedError(WebView v, WebResourceRequest req, WebResourceError err) {
                if (req != null && req.isForMainFrame()) {
                    v.loadData(offlinePage(), "text/html; charset=utf-8", "UTF-8");
                }
            }
        });
        web.loadUrl(HOME);
        setContentView(web);
    }

    private String offlinePage() {
        return "<!DOCTYPE html><html><head><meta name=viewport content='width=device-width,initial-scale=1'>"
            + "<style>body{margin:0;height:100vh;display:flex;flex-direction:column;align-items:center;justify-content:center;"
            + "background:#000;color:#e8e8ea;font-family:system-ui,sans-serif}div{font-size:15px;color:#8b8b93;margin-top:8px}"
            + "a{color:#7c8cff;margin-top:20px;text-decoration:none;border:1px solid #2a2a35;padding:9px 18px;border-radius:10px}</style></head>"
            + "<body><h3>网络不可用</h3><div>已缓存的页面仍可浏览，联网后自动恢复</div>"
            + "<a href='" + HOME + "'>重新加载</a></body></html>";
    }

    @Override
    public boolean onKeyDown(int keyCode, KeyEvent event) {
        if (keyCode == KeyEvent.KEYCODE_BACK && web != null && web.canGoBack()) {
            web.goBack();
            return true;
        }
        return super.onKeyDown(keyCode, event);
    }
}
