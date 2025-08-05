"""
Data Analysis Service for analyzing execution result data
"""
import logging
from typing import Dict, Any, List, Optional
import statistics
from collections import Counter
from datetime import datetime

logger = logging.getLogger(__name__)

class DataAnalysisService:
    """Service for analyzing execution result data"""
    
    def analyze_data(self, data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyze execution result data and return insights
        
        Args:
            data: List of data rows from execution results
            
        Returns:
            Analysis results including statistics and insights
        """
        if not data or not isinstance(data, list) or len(data) == 0:
            return {
                "summary": {
                    "row_count": 0,
                    "column_count": 0,
                    "data_quality": "No data available"
                },
                "column_stats": {},
                "insights": []
            }
        
        # Get column information
        columns = list(data[0].keys()) if data else []
        row_count = len(data)
        
        # Analyze each column
        column_stats = {}
        for column in columns:
            column_stats[column] = self._analyze_column(data, column)
        
        # Generate insights
        insights = self._generate_insights(data, column_stats)
        
        # Data quality assessment
        data_quality = self._assess_data_quality(data, column_stats)
        
        return {
            "summary": {
                "row_count": row_count,
                "column_count": len(columns),
                "data_quality": data_quality,
                "analysis_timestamp": datetime.utcnow().isoformat()
            },
            "column_stats": column_stats,
            "insights": insights,
            "correlations": self._find_correlations(data, columns)
        }
    
    def _analyze_column(self, data: List[Dict], column: str) -> Dict[str, Any]:
        """Analyze a single column of data"""
        values = [row.get(column) for row in data if row.get(column) is not None]
        
        if not values:
            return {
                "type": "empty",
                "null_count": len(data),
                "null_percentage": 100.0
            }
        
        # Determine data type
        data_type = self._determine_data_type(values)
        
        stats = {
            "type": data_type,
            "null_count": len(data) - len(values),
            "null_percentage": ((len(data) - len(values)) / len(data)) * 100 if len(data) > 0 else 0,
            "unique_count": len(set(values)),
            "unique_percentage": (len(set(values)) / len(values)) * 100 if len(values) > 0 else 0
        }
        
        if data_type == "numeric":
            numeric_values = [float(v) for v in values if self._is_numeric(v)]
            if numeric_values:
                stats.update({
                    "min": min(numeric_values),
                    "max": max(numeric_values),
                    "mean": statistics.mean(numeric_values),
                    "median": statistics.median(numeric_values),
                    "std_dev": statistics.stdev(numeric_values) if len(numeric_values) > 1 else 0,
                    "sum": sum(numeric_values)
                })
                
                # Add quartiles
                if len(numeric_values) >= 4:
                    sorted_values = sorted(numeric_values)
                    n = len(sorted_values)
                    stats["q1"] = sorted_values[n // 4]
                    stats["q3"] = sorted_values[3 * n // 4]
                    stats["iqr"] = stats["q3"] - stats["q1"]
        
        elif data_type == "categorical":
            # Get top values
            value_counts = Counter(values)
            top_values = value_counts.most_common(10)
            stats["top_values"] = [
                {"value": str(val), "count": count, "percentage": (count / len(values)) * 100}
                for val, count in top_values
            ]
            stats["mode"] = top_values[0][0] if top_values else None
            
        elif data_type == "datetime":
            # Try to parse dates
            date_values = []
            for v in values:
                try:
                    if isinstance(v, str):
                        # Try common date formats
                        for fmt in ["%Y-%m-%d", "%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S"]:
                            try:
                                date_values.append(datetime.strptime(v, fmt))
                                break
                            except:
                                continue
                except:
                    pass
            
            if date_values:
                stats["earliest"] = min(date_values).isoformat()
                stats["latest"] = max(date_values).isoformat()
                stats["date_range_days"] = (max(date_values) - min(date_values)).days
        
        return stats
    
    def _determine_data_type(self, values: List) -> str:
        """Determine the data type of a column"""
        if not values:
            return "empty"
        
        # Check if all values are numeric
        numeric_count = sum(1 for v in values if self._is_numeric(v))
        if numeric_count / len(values) > 0.8:  # 80% numeric threshold
            return "numeric"
        
        # Check if values look like dates
        date_patterns = ["%Y-%m-%d", "%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S"]
        date_count = 0
        for v in values[:min(100, len(values))]:  # Sample first 100 values
            if isinstance(v, str):
                for pattern in date_patterns:
                    try:
                        datetime.strptime(v, pattern)
                        date_count += 1
                        break
                    except:
                        continue
        
        if date_count / min(100, len(values)) > 0.5:  # 50% date threshold
            return "datetime"
        
        # Default to categorical
        return "categorical"
    
    def _is_numeric(self, value) -> bool:
        """Check if a value is numeric"""
        try:
            float(value)
            return True
        except (ValueError, TypeError):
            return False
    
    def _generate_insights(self, data: List[Dict], column_stats: Dict) -> List[Dict[str, str]]:
        """Generate insights from the data analysis"""
        insights = []
        
        # Check for high null percentages
        for column, stats in column_stats.items():
            if stats.get("null_percentage", 0) > 50:
                insights.append({
                    "type": "data_quality",
                    "severity": "warning",
                    "message": f"Column '{column}' has {stats['null_percentage']:.1f}% null values"
                })
        
        # Check for low cardinality in large datasets
        if len(data) > 100:
            for column, stats in column_stats.items():
                if stats.get("type") == "categorical" and stats.get("unique_count", 0) < 5:
                    insights.append({
                        "type": "cardinality",
                        "severity": "info",
                        "message": f"Column '{column}' has low cardinality with only {stats['unique_count']} unique values"
                    })
        
        # Check for potential outliers in numeric columns
        for column, stats in column_stats.items():
            if stats.get("type") == "numeric" and "iqr" in stats and stats["iqr"] > 0:
                q1 = stats.get("q1", 0)
                q3 = stats.get("q3", 0)
                iqr = stats.get("iqr", 0)
                lower_bound = q1 - 1.5 * iqr
                upper_bound = q3 + 1.5 * iqr
                
                outlier_count = sum(
                    1 for row in data 
                    if self._is_numeric(row.get(column)) and 
                    (float(row.get(column)) < lower_bound or float(row.get(column)) > upper_bound)
                )
                
                if outlier_count > 0:
                    insights.append({
                        "type": "outliers",
                        "severity": "info",
                        "message": f"Column '{column}' has {outlier_count} potential outliers"
                    })
        
        # Check for data patterns
        if len(data) > 0:
            # Check if data appears to be time series
            date_columns = [col for col, stats in column_stats.items() if stats.get("type") == "datetime"]
            if date_columns:
                insights.append({
                    "type": "pattern",
                    "severity": "info",
                    "message": f"Data contains time-based columns: {', '.join(date_columns)}"
                })
        
        return insights
    
    def _assess_data_quality(self, data: List[Dict], column_stats: Dict) -> str:
        """Assess overall data quality"""
        if not data:
            return "No data"
        
        # Calculate quality score
        quality_score = 100.0
        
        # Penalize for null values
        avg_null_percentage = statistics.mean(
            [stats.get("null_percentage", 0) for stats in column_stats.values()]
        )
        quality_score -= avg_null_percentage * 0.5
        
        # Penalize for empty columns
        empty_columns = sum(1 for stats in column_stats.values() if stats.get("type") == "empty")
        if len(column_stats) > 0:
            quality_score -= (empty_columns / len(column_stats)) * 20
        
        # Determine quality level
        if quality_score >= 90:
            return "Excellent"
        elif quality_score >= 75:
            return "Good"
        elif quality_score >= 60:
            return "Fair"
        elif quality_score >= 40:
            return "Poor"
        else:
            return "Very Poor"
    
    def _find_correlations(self, data: List[Dict], columns: List[str]) -> Dict[str, Any]:
        """Find potential correlations between numeric columns"""
        correlations = {}
        
        # Get numeric columns
        numeric_columns = [
            col for col in columns 
            if any(self._is_numeric(row.get(col)) for row in data[:min(100, len(data))])
        ]
        
        # Calculate correlations between numeric columns
        for i, col1 in enumerate(numeric_columns):
            for col2 in numeric_columns[i+1:]:
                try:
                    values1 = [float(row.get(col1)) for row in data if self._is_numeric(row.get(col1))]
                    values2 = [float(row.get(col2)) for row in data if self._is_numeric(row.get(col2))]
                    
                    if len(values1) == len(values2) and len(values1) > 2:
                        # Simple correlation coefficient calculation
                        mean1 = statistics.mean(values1)
                        mean2 = statistics.mean(values2)
                        
                        numerator = sum((v1 - mean1) * (v2 - mean2) for v1, v2 in zip(values1, values2))
                        denominator1 = sum((v - mean1) ** 2 for v in values1)
                        denominator2 = sum((v - mean2) ** 2 for v in values2)
                        
                        if denominator1 > 0 and denominator2 > 0:
                            correlation = numerator / (denominator1 * denominator2) ** 0.5
                            
                            if abs(correlation) > 0.5:  # Only report significant correlations
                                correlations[f"{col1}_vs_{col2}"] = {
                                    "correlation": round(correlation, 3),
                                    "strength": "strong" if abs(correlation) > 0.7 else "moderate"
                                }
                except Exception as e:
                    logger.debug(f"Could not calculate correlation for {col1} vs {col2}: {e}")
        
        return correlations
    
    def get_summary_statistics(self, data: List[Dict]) -> Dict[str, Any]:
        """Get quick summary statistics for the data"""
        if not data:
            return {"error": "No data provided"}
        
        return {
            "row_count": len(data),
            "column_count": len(data[0].keys()) if data else 0,
            "columns": list(data[0].keys()) if data else [],
            "sample_rows": data[:5] if len(data) > 5 else data
        }

# Global instance
data_analysis_service = DataAnalysisService()