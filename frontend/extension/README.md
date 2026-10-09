# Browser capture

With the backend running on 127.0.0.1:8000, open Chrome or Edge's Extensions page, enable Developer mode, and choose **Load unpacked** for this folder. Pin Job Hunt OS Capture.

Click the extension on a job listing or LinkedIn profile. It reads the visible heading and job structured metadata only after that click. Choose a country and company, check the fields, choose the CV, and confirm. It creates a saved job/application or contact in the same API as the app. Company names are reviewed, not inferred from arbitrary page text. Contact email is entered manually.

Optional submission hints require explicit permission for Greenhouse and Lever. They look for confirmation text and show a badge; they never submit an application or save a record automatically. Reload supported job tabs after enabling or disabling hints. Confirmation pages without job details need manual correction. Other job boards support manual capture, not automatic submission detection.

This extension uses Chrome Manifest V3 directly and needs no separate build or paid services. No extension store account or subscription is required for local installation. Detection is heuristic and may miss site-specific changes.
