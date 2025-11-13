# Apache Superset Dashboards Guide

This document provides comprehensive information about the four interactive dashboards built for the GoodNote Analytics Platform.

---

## Table of Contents

1. [Dashboard Overview](#dashboard-overview)
2. [Dashboard 1: Executive Overview](#dashboard-1-executive-overview)
3. [Dashboard 2: User Engagement Deep Dive](#dashboard-2-user-engagement-deep-dive)
4. [Dashboard 3: Performance Monitoring](#dashboard-3-performance-monitoring)
5. [Dashboard 4: Session Analytics](#dashboard-4-session-analytics)
6. [Common Features](#common-features)
7. [Dashboard Customization](#dashboard-customization)

---

## Dashboard Overview

### Purpose
The Superset dashboards provide interactive, real-time insights into:
- User engagement and retention
- App performance metrics
- Session behavior patterns
- Anomaly detection and alerts

### Access
- **URL:** http://localhost:8088
- **Username:** admin
- **Password:** admin

### Data Source
All dashboards query the PostgreSQL analytics database (`goodnote_analytics` schema) which is populated by Spark ETL jobs.

### Refresh Schedule
- **Executive Overview:** Hourly
- **User Engagement:** Every 6 hours
- **Performance Monitoring:** Every 30 minutes
- **Session Analytics:** Every 6 hours

---

## Dashboard 1: Executive Overview

### Purpose
High-level KPIs and trends for executive decision-making.

### Target Audience
- C-level executives
- Product managers
- Business stakeholders

### Layout

```
┌─────────────────────────────────────────────────────────────┐
│  GoodNote Analytics - Executive Dashboard                   │
│  [Date Filter: Last 30 Days ▼] [Country: All ▼]           │
├─────────────────────────────────────────────────────────────┤
│  ┌───────────────┐  ┌───────────────┐  ┌───────────────┐  │
│  │     DAU       │  │     MAU       │  │  Stickiness   │  │
│  │   125,430     │  │  1,245,678    │  │    10.07%     │  │
│  │   ↑ +5.2%     │  │   ↑ +12.3%    │  │   ↓ -2.1%     │  │
│  └───────────────┘  └───────────────┘  └───────────────┘  │
│                                                             │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  DAU/MAU Trend (Last 90 Days)                        │  │
│  │  [Line Chart: Dual Y-axis]                           │  │
│  │                                                       │  │
│  │     1.5M ┤                              ╭─ MAU       │  │
│  │     1.0M ┤        ╭─────────────────────╯            │  │
│  │     500K ┤   ╭────╯                                  │  │
│  │     200K ┤───┼─────────────────────── DAU            │  │
│  │          └───┴───┴───┴───┴───┴───┴───┴───┴          │  │
│  │          Jan  Feb  Mar  Apr  May  Jun  Jul  Aug      │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                             │
│  ┌───────────────────────┐  ┌───────────────────────────┐ │
│  │ Top 5 Countries       │  │ Device Distribution       │ │
│  │ [Horizontal Bar]      │  │ [Donut Chart]             │ │
│  │                       │  │                           │ │
│  │ US      ████████ 35%  │  │   iPhone: 35%             │ │
│  │ UK      ██████ 18%    │  │   iPad: 25%               │ │
│  │ CA      ████ 12%      │  │   Android: 20%            │ │
│  │ AU      ███ 10%       │  │   Windows: 15%            │ │
│  │ DE      ██ 8%         │  │   Mac: 5%                 │ │
│  └───────────────────────┘  └───────────────────────────┘ │
│                                                             │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Geographic Heatmap (World Map)                      │  │
│  │  [Darker = More Active Users]                        │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

### Charts

#### 1.1 DAU KPI Card
- **Type:** Big Number with Trend
- **Metric:** Daily Active Users (most recent day)
- **Comparison:** vs. previous day (%)
- **Color:** Green (positive), Red (negative)

**SQL Query:**
```sql
WITH recent_dau AS (
  SELECT date, dau,
    LAG(dau, 1) OVER (ORDER BY date) as prev_dau
  FROM goodnote_analytics.daily_active_users
  WHERE date >= CURRENT_DATE - INTERVAL '30 days'
  ORDER BY date DESC
  LIMIT 1
)
SELECT
  dau as "Current DAU",
  ROUND(100.0 * (dau - prev_dau) / prev_dau, 2) as "Change %"
FROM recent_dau;
```

#### 1.2 MAU KPI Card
- **Type:** Big Number with Trend
- **Metric:** Monthly Active Users (current month)
- **Comparison:** vs. previous month (%)

**SQL Query:**
```sql
WITH recent_mau AS (
  SELECT month, mau,
    LAG(mau, 1) OVER (ORDER BY month) as prev_mau
  FROM goodnote_analytics.monthly_active_users
  ORDER BY month DESC
  LIMIT 1
)
SELECT
  mau as "Current MAU",
  ROUND(100.0 * (mau - prev_mau) / prev_mau, 2) as "Change %"
FROM recent_mau;
```

#### 1.3 Stickiness KPI Card
- **Type:** Big Number
- **Metric:** DAU/MAU Ratio (%)
- **Interpretation:** Higher = Better user retention

**SQL Query:**
```sql
WITH metrics AS (
  SELECT
    AVG(d.dau)::BIGINT as avg_dau,
    m.mau
  FROM goodnote_analytics.daily_active_users d
  JOIN goodnote_analytics.monthly_active_users m
    ON DATE_TRUNC('month', d.date) = m.month
  WHERE m.month = DATE_TRUNC('month', CURRENT_DATE)
  GROUP BY m.mau
)
SELECT ROUND(100.0 * avg_dau / mau, 2) as "Stickiness %"
FROM metrics;
```

#### 1.4 DAU/MAU Trend (Time Series)
- **Type:** Mixed Line Chart (dual Y-axis)
- **Metrics:** DAU (daily), MAU (monthly)
- **Time Range:** Last 90 days
- **Interactivity:** Hover for exact values, zoom, pan

**Configuration:**
- X-Axis: Date
- Y-Axis (Left): DAU (0 to max)
- Y-Axis (Right): MAU (0 to max)
- Colors: DAU (blue), MAU (green)
- Markers: Enabled
- Tooltip: Show date, DAU, MAU

#### 1.5 Top Countries (Bar Chart)
- **Type:** Horizontal Bar Chart
- **Metric:** Total active users by country
- **Limit:** Top 5 countries
- **Sorting:** Descending by user count

**SQL Query:**
```sql
SELECT
  country,
  COUNT(DISTINCT user_id) as active_users,
  ROUND(100.0 * COUNT(DISTINCT user_id) / SUM(COUNT(DISTINCT user_id)) OVER (), 2) as percentage
FROM goodnote_analytics.user_engagement_summary
GROUP BY country
ORDER BY active_users DESC
LIMIT 5;
```

#### 1.6 Device Distribution (Donut Chart)
- **Type:** Donut/Pie Chart
- **Metric:** User distribution by device type
- **Labels:** Device type + percentage

**SQL Query:**
```sql
SELECT
  device_type,
  COUNT(DISTINCT user_id) as user_count
FROM goodnote_analytics.user_engagement_summary
GROUP BY device_type
ORDER BY user_count DESC;
```

#### 1.7 Geographic Heatmap
- **Type:** World Map
- **Metric:** Active users per country
- **Color Scale:** Light (fewer users) to Dark (more users)

### Filters
- **Date Range:** Last 7 days, 30 days, 90 days, custom
- **Country:** All, or specific countries (multi-select)

### Key Insights
- **Stickiness >10%** indicates healthy user engagement
- **DAU trend** shows daily volatility and patterns (weekday vs. weekend)
- **MAU trend** shows overall growth trajectory
- **Geographic distribution** informs localization priorities
- **Device mix** guides platform-specific optimization

---

## Dashboard 2: User Engagement Deep Dive

### Purpose
Detailed analysis of user behavior, retention, and engagement patterns.

### Target Audience
- Product managers
- Growth teams
- Data analysts

### Layout

```
┌─────────────────────────────────────────────────────────────┐
│  User Engagement Analysis                                    │
│  [Date: Last 6 Months ▼] [Country ▼] [Device ▼] [Sub ▼]   │
├─────────────────────────────────────────────────────────────┤
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Cohort Retention Heatmap (Weekly Cohorts)           │  │
│  │                                                       │  │
│  │  Cohort Week   W0   W1   W2   W3   W4   W5   W6     │  │
│  │  2023-W01     100%  65%  52%  48%  45%  43%  41%     │  │
│  │  2023-W02     100%  68%  55%  51%  48%  46%  44%     │  │
│  │  2023-W03     100%  70%  58%  54%  51%  49%  47%     │  │
│  │  ...                                                  │  │
│  │                                                       │  │
│  │  Color: 🟩 Green (high) → 🟨 Yellow → 🟥 Red (low)   │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                             │
│  ┌───────────────────────┐  ┌───────────────────────────┐ │
│  │ Power Users (Top 1%) │  │ Engagement Score          │ │
│  │ [Sortable Table]      │  │ Distribution (Histogram)  │ │
│  │                       │  │                           │ │
│  │ User ID  | Hours     │  │    Count                  │ │
│  │ u000042  | 1,234     │  │    1000 ┤    ╭─╮          │ │
│  │ u000137  | 1,156     │  │     800 ┤   ╭╯ ╰╮         │ │
│  │ u000891  | 1,089     │  │     600 ┤  ╭╯   ╰╮        │ │
│  │ u001234  | 1,045     │  │     400 ┤ ╭╯     ╰╮       │ │
│  │ u002567  | 1,012     │  │     200 ┤╭╯       ╰─╮     │ │
│  │ ...      | ...       │  │         └┴──┴──┴──┴──┴    │ │
│  │                       │  │         0  25  50  75 100 │ │
│  │ [Download CSV]        │  │         Engagement Score  │ │
│  └───────────────────────┘  └───────────────────────────┘ │
│                                                             │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Actions per Session (Box Plot by Device Type)       │  │
│  │                                                       │  │
│  │  iPhone    [▬▬▬▬█████▬▬]                             │  │
│  │  iPad      [▬▬▬████████▬]                            │  │
│  │  Android   [▬▬███████▬▬]                             │  │
│  │  Windows   [▬████████▬▬]                             │  │
│  │                                                       │  │
│  │  Min  Q1  Median  Q3  Max  Outliers                  │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

### Charts

#### 2.1 Cohort Retention Heatmap
- **Type:** Heatmap
- **Rows:** Cohort weeks (past 6 months)
- **Columns:** Weeks since cohort start (W0 to W24)
- **Values:** Retention rate (%)
- **Colors:** Gradient from red (low) to green (high)

**SQL Query:**
```sql
SELECT
  cohort_week,
  week_number,
  ROUND(retention_rate, 1) as retention_pct
FROM goodnote_analytics.cohort_retention
WHERE cohort_week >= CURRENT_DATE - INTERVAL '6 months'
ORDER BY cohort_week DESC, week_number ASC;
```

**Interpretation:**
- W0 = 100% (all users start active)
- Steep drop from W0 to W1 is normal (typical: 30-40% drop)
- Flattening curve after W4 indicates stabilization
- Compare cohorts: Are newer cohorts retaining better?

#### 2.2 Power Users Table
- **Type:** Sortable Table
- **Columns:** User ID, Total Hours, Interactions, Device, Subscription, Country
- **Row Limit:** 1000 (paginated)
- **Features:** Sort, filter, download CSV

**SQL Query:**
```sql
SELECT
  user_id,
  ROUND(total_duration_ms / 3600000.0, 1) as hours_spent,
  total_interactions,
  device_type,
  subscription_type,
  country,
  ROUND(engagement_score, 2) as score
FROM goodnote_analytics.power_users
ORDER BY hours_spent DESC
LIMIT 1000;
```

**Use Cases:**
- Identify VIP users for beta testing
- Reach out for user interviews
- Analyze common patterns among power users

#### 2.3 Engagement Score Distribution
- **Type:** Histogram
- **Metric:** User engagement score
- **Bins:** 20 bins (0-100 score range)
- **Overlay:** Normal distribution curve

**SQL Query:**
```sql
SELECT
  FLOOR(engagement_score / 5) * 5 as score_bucket,
  COUNT(*) as user_count
FROM goodnote_analytics.user_engagement_summary
GROUP BY score_bucket
ORDER BY score_bucket;
```

#### 2.4 Actions per Session (Box Plot)
- **Type:** Box Plot
- **Grouping:** Device type
- **Metric:** Actions per session (count)
- **Shows:** Min, Q1, Median, Q3, Max, Outliers

**SQL Query:**
```sql
SELECT
  device_type,
  avg_actions_per_session
FROM goodnote_analytics.session_analytics
WHERE date >= CURRENT_DATE - INTERVAL '30 days';
```

### Filters
- **Date Range:** Last 30 days, 90 days, 6 months, 1 year
- **Country:** Multi-select dropdown
- **Device Type:** Multi-select dropdown
- **Subscription Type:** Free, Basic, Premium, Enterprise

### Key Insights
- **W1 Retention >60%** indicates strong onboarding
- **W4 Retention >40%** indicates product-market fit
- **Power users** drive 80% of engagement (Pareto principle)
- **Device differences** inform platform prioritization

---

## Dashboard 3: Performance Monitoring

### Purpose
Monitor app performance metrics and identify issues.

### Target Audience
- Engineering teams
- DevOps
- Platform teams

### Layout

```
┌─────────────────────────────────────────────────────────────┐
│  App Performance Dashboard                                   │
│  [Date: Last 7 Days ▼] [Version ▼] [Device ▼]             │
├─────────────────────────────────────────────────────────────┤
│  ┌──────────────────────────────────────────────────────┐  │
│  │  P95 Load Time by App Version (Time Series)          │  │
│  │  [With Alert Threshold Line]                          │  │
│  │                                                       │  │
│  │  3000ms ┤                        ⚠ Alert Threshold   │  │
│  │  2500ms ┤─────────────────────────────────────────   │  │
│  │  2000ms ┤            ╭─╮                             │  │
│  │  1500ms ┤        ╭───╯ ╰─╮                           │  │
│  │  1000ms ┤    ╭───╯       ╰───╮                       │  │
│  │   500ms ┤────╯               ╰──────                 │  │
│  │         └────┴────┴────┴────┴────┴────┴             │  │
│  │         v5.7 v5.8 v5.9 v6.0 v6.1 v6.2                │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                             │
│  ┌───────────────────────┐  ┌───────────────────────────┐ │
│  │ Device Performance    │  │ Version Comparison        │ │
│  │ Correlation Matrix    │  │ (Grouped Bar Chart)       │ │
│  │                       │  │                           │ │
│  │      Dur  Int  Crash  │  │      P50  P95  P99        │ │
│  │ Dur  1.0  0.7  0.3    │  │ v6.2 █    ██   ███        │ │
│  │ Int  0.7  1.0  0.2    │  │ v6.1 ██   ███  ████       │ │
│  │ Crash 0.3  0.2  1.0   │  │ v6.0 ███  ████ █████      │ │
│  │                       │  │ v5.9 ████ █████ ██████    │ │
│  └───────────────────────┘  └───────────────────────────┘ │
│                                                             │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Recent Anomalies (Last 24 Hours)                    │  │
│  │  [Sortable Table with Severity Color Coding]         │  │
│  │                                                       │  │
│  │  Time       | Type    | Severity | Description       │  │
│  │  10:32 AM   | Latency | 🔴 HIGH  | P95 spike +200%   │  │
│  │  09:15 AM   | Error   | 🟡 MED   | 500 errors +50%   │  │
│  │  08:45 AM   | Usage   | 🟢 LOW   | Unusual traffic   │  │
│  │  ...        | ...     | ...      | ...               │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

### Charts

#### 3.1 P95 Load Time Trend
- **Type:** Time Series Line Chart
- **Metric:** 95th percentile duration (ms)
- **Grouping:** App version
- **Alert Line:** 2500ms threshold

**SQL Query:**
```sql
SELECT
  date,
  app_version,
  p95_duration_ms
FROM goodnote_analytics.performance_by_version
WHERE date >= CURRENT_DATE - INTERVAL '30 days'
  AND p95_duration_ms < 10000  -- Filter outliers
ORDER BY date, app_version;
```

#### 3.2 Device Performance Correlation Matrix
- **Type:** Heatmap (Correlation Matrix)
- **Metrics:** Duration, Interactions, Crash Rate
- **Values:** Pearson correlation (-1 to 1)

**SQL Query:**
```sql
-- Aggregated metrics by device
SELECT
  device_type,
  AVG(avg_duration_ms) as avg_duration,
  AVG(total_interactions) as avg_interactions,
  AVG(crash_rate) as avg_crash_rate
FROM goodnote_analytics.device_performance
WHERE date >= CURRENT_DATE - INTERVAL '30 days'
GROUP BY device_type;
```

#### 3.3 Version Comparison (Bar Chart)
- **Type:** Grouped Bar Chart
- **Metrics:** P50, P95, P99 load times
- **Grouping:** App version (last 5 versions)

**SQL Query:**
```sql
SELECT
  app_version,
  AVG(p50_duration_ms) as p50,
  AVG(p95_duration_ms) as p95,
  AVG(p99_duration_ms) as p99
FROM goodnote_analytics.performance_by_version
WHERE date >= CURRENT_DATE - INTERVAL '30 days'
  AND app_version IN (SELECT DISTINCT app_version
                      FROM goodnote_analytics.performance_by_version
                      ORDER BY app_version DESC LIMIT 5)
GROUP BY app_version
ORDER BY app_version DESC;
```

#### 3.4 Recent Anomalies Table
- **Type:** Table with Conditional Formatting
- **Columns:** Timestamp, Type, Severity, Description
- **Sorting:** Most recent first
- **Colors:** Red (critical), Yellow (medium), Green (low)

**SQL Query:**
```sql
SELECT
  timestamp,
  anomaly_type,
  severity,
  description,
  actual_value,
  expected_value,
  ROUND(z_score, 2) as z_score
FROM goodnote_analytics.usage_anomalies
WHERE timestamp >= NOW() - INTERVAL '24 hours'
ORDER BY timestamp DESC, severity DESC
LIMIT 50;
```

### Alerts
- **P95 > 2500ms:** Email alert to engineering team
- **Crash rate > 1%:** Slack notification
- **Anomaly severity = critical:** PagerDuty alert

### Key Insights
- **P95 < 2000ms** is target for good UX
- **Newer versions should improve performance** (downward trend)
- **Device correlation** shows if hardware impacts performance
- **Anomalies** require immediate investigation

---

## Dashboard 4: Session Analytics

### Purpose
Understand user session patterns and behavior flows.

### Target Audience
- Product managers
- UX designers
- Data analysts

### Layout

```
┌─────────────────────────────────────────────────────────────┐
│  Session Behavior Analysis                                   │
│  [Date: Last 30 Days ▼] [Country ▼] [Device ▼]            │
├─────────────────────────────────────────────────────────────┤
│  ┌───────────────────────┐  ┌───────────────────────────┐ │
│  │ Avg Session Duration  │  │ Sessions per User         │ │
│  │ (Treemap by Country)  │  │ (Bubble Chart)            │ │
│  │                       │  │                           │ │
│  │ ┌────┬────┬─────┐    │  │        ○                  │ │
│  │ │ US │ UK │ CA  │    │  │   ○        ○              │ │
│  │ ├────┼────┴─────┤    │  │      ○   ○                │ │
│  │ │ AU │   DE     │    │  │  ○     ○      ○           │ │
│  │ ├────┴──────────┤    │  │                           │ │
│  │ │      FR       │    │  │  Size = Avg Duration      │ │
│  │ └───────────────┘    │  │  Color = Bounce Rate      │ │
│  └───────────────────────┘  └───────────────────────────┘ │
│                                                             │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Action Type Distribution Over Time                   │  │
│  │  [Stacked Area Chart]                                 │  │
│  │                                                       │  │
│  │   100% ┤─────────────────────────────────────────    │  │
│  │    75% ┤███████ share                                │  │
│  │    50% ┤█████████ delete                             │  │
│  │    25% ┤███████████ create                           │  │
│  │        ┤█████████████ edit                           │  │
│  │     0% ┤███████████████ page_view                    │  │
│  │        └────┴────┴────┴────┴────┴────┴              │  │
│  │        Jan  Feb  Mar  Apr  May  Jun  Jul            │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                             │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Bounce Rate Analysis                                 │  │
│  │  [Grouped Bar Chart with Dual Axis]                  │  │
│  │                                                       │  │
│  │      iPhone  iPad  Android Windows  Mac              │  │
│  │ Free   35%    28%   42%     38%     32%              │  │
│  │ Prem   18%    15%   22%     20%     16%              │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

### Charts

#### 4.1 Session Duration Treemap
- **Type:** Treemap
- **Grouping:** Country
- **Size:** Average session duration
- **Color:** Gradient (darker = longer sessions)

**SQL Query:**
```sql
SELECT
  country,
  ROUND(AVG(avg_session_duration_ms) / 60000.0, 1) as avg_duration_minutes,
  SUM(total_sessions) as total_sessions
FROM goodnote_analytics.session_analytics
WHERE date >= CURRENT_DATE - INTERVAL '30 days'
GROUP BY country
ORDER BY avg_duration_minutes DESC;
```

#### 4.2 Sessions per User (Bubble Chart)
- **Type:** Bubble Chart
- **X-Axis:** Device type
- **Y-Axis:** Subscription type
- **Size:** Average session duration
- **Color:** Bounce rate (red = high, green = low)

**SQL Query:**
```sql
SELECT
  device_type,
  subscription_type,
  AVG(sessions_per_user) as avg_sessions,
  AVG(avg_session_duration_ms) as avg_duration,
  AVG(bounce_rate) as avg_bounce_rate
FROM goodnote_analytics.session_analytics
WHERE date >= CURRENT_DATE - INTERVAL '30 days'
GROUP BY device_type, subscription_type;
```

#### 4.3 Action Type Distribution
- **Type:** Stacked Area Chart (100%)
- **Metrics:** Action type proportions over time
- **Categories:** page_view, edit, create, delete, share

**SQL Query:**
```sql
SELECT
  date,
  action_type,
  SUM(total_actions) as action_count
FROM goodnote_analytics.action_distribution
WHERE date >= CURRENT_DATE - INTERVAL '90 days'
GROUP BY date, action_type
ORDER BY date, action_type;
```

#### 4.4 Bounce Rate Analysis
- **Type:** Grouped Bar Chart
- **Grouping:** Device type (X-axis), Subscription type (series)
- **Metric:** Bounce rate (%)

**SQL Query:**
```sql
SELECT
  device_type,
  subscription_type,
  ROUND(AVG(bounce_rate), 1) as avg_bounce_rate
FROM goodnote_analytics.session_analytics
WHERE date >= CURRENT_DATE - INTERVAL '30 days'
GROUP BY device_type, subscription_type
ORDER BY device_type, subscription_type;
```

### Filters
- **Date Range:** Last 7 days, 30 days, 90 days
- **Country:** Multi-select
- **Device Type:** Multi-select
- **Subscription Type:** Multi-select

### Key Insights
- **Longer sessions** indicate higher engagement
- **Low bounce rate** (<25%) is healthy
- **Action distribution** shows feature usage patterns
- **Premium users** typically have longer sessions and lower bounce rates

---

## Common Features

### Native Filters
All dashboards support native filters that apply across all charts:
- **Date Range Picker:** Visual calendar interface
- **Multi-Select Dropdowns:** Filter by multiple values
- **Search:** Filter large lists (countries, users)

### Cross-Filtering
Click on any chart element to filter other charts:
- Click country on map → Filter all charts to that country
- Click date on time-series → Filter to that date

### Drill-Down
Right-click on data points to drill into details:
- Dashboard → Detailed table view
- Aggregated metric → Individual records

### Export Options
- **CSV:** Export table data
- **PNG/PDF:** Export chart images
- **Dashboard PDF:** Export entire dashboard

### Scheduled Reports
Configure email reports:
- **Frequency:** Daily, weekly, monthly
- **Recipients:** Email list
- **Format:** PDF attachment
- **Time:** Configurable delivery time

---

## Dashboard Customization

### Creating New Charts

1. **Navigate to SQL Lab:**
   - Click "SQL Lab" → "SQL Editor"
   - Connect to "GoodNote Analytics" database

2. **Write SQL Query:**
   ```sql
   SELECT
     date,
     COUNT(DISTINCT user_id) as active_users
   FROM goodnote_analytics.daily_active_users
   GROUP BY date
   ORDER BY date;
   ```

3. **Save as Dataset:**
   - Click "Save" → "Save as Dataset"
   - Name: "Custom Active Users"

4. **Create Chart:**
   - Click "Charts" → "New Chart"
   - Select dataset: "Custom Active Users"
   - Choose visualization type
   - Configure metrics and dimensions
   - Save chart

5. **Add to Dashboard:**
   - Open dashboard in edit mode
   - Drag chart from left panel
   - Resize and position
   - Save dashboard

### Modifying Existing Charts

1. **Edit Chart:**
   - Open dashboard
   - Click "⋮" on chart → "Edit chart"
   - Modify query, metrics, or visualization
   - Save changes

2. **Chart Properties:**
   - Colors, fonts, labels
   - Axis ranges and scales
   - Tooltips and legends

### Best Practices

1. **Performance:**
   - Limit queries to <100K rows
   - Use aggregated tables when possible
   - Cache frequently accessed queries

2. **Usability:**
   - Clear chart titles and labels
   - Consistent color schemes
   - Appropriate chart types for data

3. **Maintenance:**
   - Document complex SQL queries
   - Version control dashboard exports (JSON)
   - Regular review and cleanup

---

## Troubleshooting

### Chart Shows "No Data"
- Verify data exists in PostgreSQL
- Check filters aren't too restrictive
- Clear cache: Chart → ⋮ → "Force Refresh"

### Slow Query Performance
- Add indexes to frequently queried columns
- Reduce date range in filter
- Use pre-aggregated tables

### Chart Not Rendering
- Check browser console for errors
- Verify database connection is active
- Restart Superset: `docker-compose restart superset`

---

## Additional Resources

- **Superset Documentation:** https://superset.apache.org/docs/intro
- **SQL Lab Guide:** https://superset.apache.org/docs/creating-charts-dashboards/creating-your-first-dashboard
- **Custom Visualization:** https://superset.apache.org/docs/contributing/plugins

---

**Document Version:** 1.0
**Last Updated:** 2025-11-13
**Dashboard Count:** 4
**Total Charts:** 30+
