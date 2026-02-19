# TikTok Insight Analytics Dashboard

A premium, data-driven dashboard designed to help creators and social teams track performance, discover trends, and analyze audience engagement without the need for manual video management.

## Features
- **Real-time Analytics**: Visualize views, likes, and follower growth with interactive charts.
- **Trend Intelligence**: Stay ahead with live feeds of trending hashtags and viral sounds.
- **Audience Deep-Dive**: Understand engagement rates and watch time patterns.
- **Data Archiving**: Maintain a historical record of your TikTok performance (Ready for DB integration).

## Tech Stack
- **Frontend**: HTML5, Vanilla CSS3 (Custom Glass-theme), Javascript (ES6).
- **Charts**: Chart.js 4.x.
- **Icons**: FontAwesome 6.

## Getting Started
To connect this dashboard to your real TikTok data:
1. **TikTok Developer Account**: Sign up at [developers.tiktok.com](https://developers.tiktok.com/).
2. **Create an App**: Register a new application to get your `Client Key` and `Client Secret`.
3. **API Scopes**: Request access to `video.list`, `user.info.basic`, and `video.content.analytics`.
4. **Integration**: The `app.js` file is structured to receive data from a backend or direct API calls using these credentials.

## Design Philosophy
The UI follows a "Premium Dark" aesthetic, utilizing backdrop-blur, subtle gradients, and high-contrast typography to ensure a professional and engaging experience for data analysis.
