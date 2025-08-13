# dsp_impressions Segment Tables Schema

## Overview

**Data Sources:** 
- `dsp_impressions_by_matched_segments`
- `dsp_impressions_by_user_segments`

⚠️ **Important Performance Warning**: Workflows that use these tables will time out when run over extended periods of time.

These two tables have exactly the same basic structure as `dsp_impressions` table but in addition to that they provide segment level information for each of the segments that was either targeted by the ad or included the user that received the impression. This means that **each impression appears multiple times in these tables**.

## Table Differences

### dsp_impressions_by_matched_segments
Shows only the segments that included the user **AND** were targeted by the ad at the time of the impression.

### dsp_impressions_by_user_segments  
Shows **ALL** segments that include the user. The `behavior_segment_matched` field is set to "1" if the segment was targeted by the ad, "0" if not.

## Base Structure

Both tables inherit **ALL columns from the `dsp_impressions` table**, plus the additional segment-specific columns listed below.

For the complete base schema, refer to the [dsp_impressions documentation](#).

## Additional Segment Columns

| Name | Data Type | Metric / Dimension | Description | Aggregation Threshold |
|------|-----------|-------------------|-------------|----------------------|
| behavior_segment_description | STRING | Dimension | Description of the audience segment, for segments both targeted by the Amazon DSP line item and matched to the user at the time of impression. This field contains explanations of the characteristics that define each segment, such as shopping behaviors, demographics, and interests. | LOW |
| behavior_segment_id | INTEGER | Dimension | Unique identifier for the audience segment, for segments both targeted by the Amazon DSP line item and matched to the user at the time of impression. Example value: '123456'. | LOW |
| behavior_segment_matched | LONG | Metric | Indicator of whether the behavior segment was targeted by the Amazon DSP line item and matched to the user at the time of impression. **For dsp_impressions_by_matched_segments**: Always '1' (segment was targeted and matched). **For dsp_impressions_by_user_segments**: '1' if targeted, '0' if not targeted. | LOW |
| behavior_segment_name | STRING | Dimension | Name of the audience segment, for segments both targeted by the Amazon DSP line item and matched to the user at the time of impression. | LOW |

## Data Structure and Usage Notes

### Record Multiplication
- **Single impression = Multiple rows**: Each impression will appear once for every relevant segment
- **Row count implications**: Total row count will be much higher than base `dsp_impressions` table
- **Aggregation considerations**: Be careful when summing impression counts to avoid double-counting

### Table Selection Guide

**Use `dsp_impressions_by_matched_segments` when:**
- You only care about segments that were both targeted AND matched
- You want to analyze performance of targeted segments
- You need cleaner data with only relevant segment matches

**Use `dsp_impressions_by_user_segments` when:**
- You want to see all segments a user belongs to
- You need to compare targeted vs non-targeted segment performance  
- You want comprehensive audience insight regardless of targeting

### Query Considerations

#### Counting Impressions
```sql
-- Correct way to count unique impressions
SELECT COUNT(DISTINCT request_tag) as unique_impressions
FROM dsp_impressions_by_matched_segments

-- Incorrect - will overcount due to segment multiplication
SELECT SUM(impressions) as total_impressions  
FROM dsp_impressions_by_matched_segments
```

#### Filtering by Segment Targeting
```sql
-- For dsp_impressions_by_user_segments only
-- Get only targeted segments
WHERE behavior_segment_matched = 1

-- Get non-targeted segments user belongs to
WHERE behavior_segment_matched = 0
```

## Performance Recommendations

- **Limit time ranges**: Use narrow date filters to prevent timeouts
- **Filter early**: Apply segment and campaign filters in WHERE clauses
- **Use sampling**: Consider sampling techniques for large datasets
- **Aggregate strategically**: Pre-aggregate data when possible
- **Monitor execution time**: Set reasonable timeout limits for queries

## Common Use Cases

### Segment Performance Analysis
- Compare performance across different audience segments
- Identify highest-performing targeted segments
- Analyze segment overlap and user behavior

### Audience Insights
- Understand which segments users belong to beyond targeting
- Discover untargeted segments with high engagement
- Optimize targeting strategy based on segment performance

### Attribution Analysis
- Track user journey across multiple segments
- Understand segment contribution to conversions
- Analyze cross-segment interaction effects

## Relationship to Other Tables

- **Base data**: All impression-level data comes from `dsp_impressions`
- **Segment expansion**: These tables "explode" each impression into multiple segment-specific records
- **Data consistency**: Impression counts should match `dsp_impressions` when properly deduplicated
- **Join considerations**: Use `request_tag` or `user_id` for joins, but be aware of the multiplied records