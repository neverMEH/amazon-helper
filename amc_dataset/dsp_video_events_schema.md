# dsp_video_events_feed Data Source Schema

## Overview

**Data Source:** `dsp_video_events_feed`

⚠️ **Important Performance Warning**: Workflows that use this table will time out when run over extended periods of time.

This table has the exact same basic structure as `dsp_impressions` table but in addition to that, the table provides video metrics for each of the video creative events triggered by the video player and associated with the impression event.

## Base Structure

This table inherits **ALL columns from the `dsp_impressions` table**, plus the additional video-specific columns listed below.

For the complete base schema, refer to the [dsp_impressions documentation](#).

## Additional Video Event Columns

| Field | Data Type | Metric / Dimension | Definition | Aggregation Threshold |
|-------|-----------|-------------------|------------|----------------------|
| video_click | LONG | Metric | The number of Amazon DSP video clicks. Possible values for this field are: '1' (if the video was clicked) or '0' (if the video was not clicked). This field will always be '0' for non-video impressions. | NONE |
| video_complete | LONG | Metric | The number of Amazon DSP video impressions where the video was viewed to completion (100%). Possible values for this field are: '1' (if the video was viewed to completion) or '0' (if the video was not viewed to completion). This field will always be '0' for non-video impressions. | NONE |
| video_creative_view | LONG | Metric | The number of Amazon DSP video impressions where an additional ad element, such as the video companion ad or VPAID overlay, was viewed. Possible values for this field are: '1' (if the additional ad element was viewed) or '0' (if the additional ad element was not viewed). This field will always be '0' for non-video impressions. | NONE |
| video_first_quartile | LONG | Metric | The number of Amazon DSP video impressions where the video was viewed to the first quartile (at least 25% completion). Possible values for this field are: '1' (if the video was viewed to at least 25% completion) or '0' (if the video was not viewed to 25% completion). This field will always be '0' for non-video impressions. | NONE |
| video_impression | LONG | Metric | The number of Amazon DSP video impressions where the first frame of the ad was shown. Possible values for this field are: '1' (if the first frame of the video was shown) or '0' (if the first frame of the video was not shown). This field will always be '0' for non-video impressions. | NONE |
| video_midpoint | LONG | Metric | The number of Amazon DSP video impressions where the video was viewed to the midpoint (at least 50% completion). Possible values for this field are: '1' (if the video was viewed to at least 50% completion) or '0' (if the video was not viewed to 50% completion). This field will always be '0' for non-video impressions. | NONE |
| video_mute | LONG | Metric | The number of Amazon DSP video mutes. Possible values for this field are: '1' (if the user muted the video) or '0' (if the user did not mute the video). This field will always be '0' for non-video impressions. | NONE |
| video_pause | LONG | Metric | The number of Amazon DSP video pauses. Possible values for this field are: '1' (if the user paused the video) or '0' (if the user did not pause the video). This field will always be '0' for non-video impressions. | NONE |
| video_replay | LONG | Metric | The number of Amazon DSP video impressions where the ad was replayed again after it completed. Possible values for this field are: '1' (if the user replayed the video after completion) or '0' (if the video was not replayed after completion). This field will always be '0' for non-video impressions. | NONE |
| video_resume | LONG | Metric | The number of Amazon DSP video impressions where the video was resumed after a pause. Possible values for this field are: '1' (if the video was resumed after a pause) or '0' (if the video was not resumed after a pause). This field will always be '0' for non-video impressions. | NONE |
| video_skip_backward | LONG | Metric | The number of Amazon DSP video impressions that had backward skips. Possible values for this field are: '1' (if the user skipped the video backward) or '0' (if the user did not skip the video backward). This field will always be '0' for non-video impressions. | NONE |
| video_skip_forward | LONG | Metric | The number of Amazon DSP video impressions that had forward skips. Possible values for this field are: '1' (if the user skipped the video forward) or '0' (if the user did not skip the video forward). This field will always be '0' for non-video impressions. | NONE |
| video_start | LONG | Metric | The number of Amazon DSP video impression starts. Possible values for this field are: '1' (if the user started the video) or '0' (if the user did not start the video). This field will always be '0' for non-video impressions. | NONE |
| video_third_quartile | LONG | Metric | The number of Amazon DSP video impressions where the video was viewed to the third quartile (at least 75% completion). Possible values for this field are: '1' (if the video was viewed to at least 75% completion) or '0' (if the video was not viewed to 75% completion). This field will always be '0' for non-video impressions. | NONE |
| video_unmute | LONG | Metric | The number of Amazon DSP video unmutes. Possible values for this field are: '1' (if the video was unmuted) or '0' (if the video was not unmuted). This field will always be '0' for non-video impressions. | NONE |

## Video Engagement Metrics Categories

### Completion Tracking
- **video_impression**: First frame shown (video started loading)
- **video_start**: User actively started the video
- **video_first_quartile**: 25% completion
- **video_midpoint**: 50% completion  
- **video_third_quartile**: 75% completion
- **video_complete**: 100% completion

### User Interactions
- **video_click**: User clicked on the video
- **video_pause**: User paused the video
- **video_resume**: User resumed after pausing
- **video_replay**: User replayed after completion

### Audio Controls
- **video_mute**: User muted the video
- **video_unmute**: User unmuted the video

### Playback Controls
- **video_skip_forward**: User skipped ahead in the video
- **video_skip_backward**: User skipped back in the video

### Additional Elements
- **video_creative_view**: Companion ad or overlay viewed

## Data Structure and Usage Notes

### Binary Metrics
- **All video metrics are binary**: Each field contains either '1' (event occurred) or '0' (event did not occur)
- **Non-video impressions**: All video metrics will be '0' for display/non-video creatives
- **Single event per impression**: Each metric represents whether that specific event happened for that impression

### Filtering Video Content
```sql
-- Get only video impressions
SELECT * FROM dsp_video_events_feed 
WHERE creative_category = 'Video'

-- Get impressions where video was started
SELECT * FROM dsp_video_events_feed 
WHERE video_start = 1

-- Get completed video views
SELECT * FROM dsp_video_events_feed 
WHERE video_complete = 1
```

### Calculating Engagement Rates
```sql
-- Video completion rate
SELECT 
    campaign,
    SUM(video_start) as video_starts,
    SUM(video_complete) as video_completions,
    CASE 
        WHEN SUM(video_start) > 0 
        THEN SUM(video_complete) * 100.0 / SUM(video_start) 
        ELSE 0 
    END as completion_rate_percent
FROM dsp_video_events_feed
WHERE creative_category = 'Video'
GROUP BY campaign;

-- Quartile drop-off analysis
SELECT 
    campaign,
    SUM(video_start) as starts,
    SUM(video_first_quartile) as q1,
    SUM(video_midpoint) as q2,
    SUM(video_third_quartile) as q3,
    SUM(video_complete) as completions
FROM dsp_video_events_feed
WHERE creative_category = 'Video'
GROUP BY campaign;
```

## Common Video Performance Analysis

### Engagement Funnel
1. **video_impression** → Video ad loaded
2. **video_start** → User began watching
3. **video_first_quartile** → 25% watched
4. **video_midpoint** → 50% watched  
5. **video_third_quartile** → 75% watched
6. **video_complete** → 100% watched

### Interaction Analysis
- **Pause/Resume Behavior**: Track user engagement patterns
- **Mute/Unmute Patterns**: Understand audio preferences
- **Skip Behavior**: Identify content issues or user preferences
- **Replay Activity**: Measure content effectiveness

## Performance Recommendations

- **Limit time ranges**: Use narrow date filters to prevent timeouts
- **Filter by video content**: Focus on `creative_category = 'Video'` when analyzing video metrics
- **Pre-aggregate data**: Summarize video events for large datasets
- **Use sampling**: Consider sampling techniques for extended analysis
- **Monitor query performance**: Set reasonable timeout limits

## Relationship to Other Tables

- **Base data**: Inherits all impression-level data from `dsp_impressions`
- **Video-specific**: Only video impressions will have meaningful video metric values
- **Event granularity**: Each row represents one impression with all associated video events
- **Join compatibility**: Can be joined with other DSP tables using standard keys like `request_tag` or `campaign_id`

## Use Cases

### Creative Optimization
- Identify which video creatives drive highest completion rates
- Analyze drop-off points to optimize video length and content
- Compare engagement across different video formats and durations

### Audience Insights
- Understand viewing behavior by audience segment
- Identify which audiences engage most with video content
- Optimize targeting based on video engagement patterns

### Campaign Performance
- Track video engagement metrics alongside impression and click data
- Calculate video-specific KPIs like completion rates and interaction rates
- Optimize video campaigns based on engagement data