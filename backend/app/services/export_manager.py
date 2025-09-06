"""
Export functionality for search results and analytics data.
"""

import json
import csv
import io
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging

try:
    import pandas as pd
    from openpyxl import Workbook
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.lib import colors
    EXPORT_DEPENDENCIES_AVAILABLE = True
except ImportError:
    EXPORT_DEPENDENCIES_AVAILABLE = False
    logger = logging.getLogger(__name__)
    logger.warning("Export dependencies not available. Some export formats may not work.")

from app.core.config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)


class ExportManager:
    """
    Comprehensive export manager supporting multiple formats and data types.
    """
    
    def __init__(self):
        self.supported_formats = ['json', 'csv', 'xlsx', 'pdf']
        if not EXPORT_DEPENDENCIES_AVAILABLE:
            self.supported_formats = ['json', 'csv']
    
    async def export_search_results(
        self,
        search_results: Dict[str, Any],
        export_format: str = 'json',
        include_metadata: bool = True,
        include_analytics: bool = False
    ) -> bytes:
        """
        Export search results in specified format.
        
        Args:
            search_results: Search results data
            export_format: Output format (json, csv, xlsx, pdf)
            include_metadata: Include query metadata
            include_analytics: Include analytics data
        
        Returns:
            Exported data as bytes
        """
        if export_format not in self.supported_formats:
            raise ValueError(f"Unsupported export format: {export_format}")
        
        # Prepare export data
        export_data = self._prepare_export_data(
            search_results, 
            include_metadata, 
            include_analytics
        )
        
        # Export based on format
        if export_format == 'json':
            return await self._export_json(export_data)
        elif export_format == 'csv':
            return await self._export_csv(export_data)
        elif export_format == 'xlsx':
            return await self._export_xlsx(export_data)
        elif export_format == 'pdf':
            return await self._export_pdf(export_data)
        else:
            raise ValueError(f"Export format {export_format} not implemented")
    
    def _prepare_export_data(
        self,
        search_results: Dict[str, Any],
        include_metadata: bool,
        include_analytics: bool
    ) -> Dict[str, Any]:
        """Prepare data for export."""
        export_data = {
            'export_info': {
                'exported_at': datetime.now().isoformat(),
                'total_videos': search_results.get('total_results', 0),
                'search_time_ms': search_results.get('search_time_ms', 0),
                'quota_used': search_results.get('quota_used', 0)
            }
        }
        
        # Include metadata if requested
        if include_metadata:
            export_data['query_metadata'] = search_results.get('query_info', {})
            export_data['suggestions'] = search_results.get('suggestions', [])
        
        # Process video data
        videos = search_results.get('videos', [])
        export_data['videos'] = []
        
        for video in videos:
            video_export = {
                'video_id': video.get('video_id', ''),
                'title': video.get('title', ''),
                'channel_title': video.get('channel_title', ''),
                'published_at': video.get('published_at', ''),
                'duration_seconds': video.get('duration'),
                'view_count': video.get('view_count', 0),
                'like_count': video.get('like_count'),
                'comment_count': video.get('comment_count'),
                'relevance_score': video.get('relevance_score', 0),
                'quality_score': video.get('quality_score', 0),
                'engagement_rate': video.get('engagement_rate'),
                'youtube_url': f"https://www.youtube.com/watch?v={video.get('video_id', '')}",
                'tags': video.get('tags', [])
            }
            
            # Include description if available
            if video.get('description'):
                # Truncate long descriptions for readability
                description = video['description']
                if len(description) > 500:
                    description = description[:500] + "..."
                video_export['description'] = description
            
            export_data['videos'].append(video_export)
        
        # Include analytics if requested
        if include_analytics:
            export_data['analytics'] = self._generate_export_analytics(videos)
        
        return export_data
    
    def _generate_export_analytics(self, videos: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate analytics summary for export."""
        if not videos:
            return {}
        
        total_views = sum(v.get('view_count', 0) for v in videos)
        total_likes = sum(v.get('like_count', 0) or 0 for v in videos)
        total_comments = sum(v.get('comment_count', 0) or 0 for v in videos)
        
        # Calculate averages
        avg_views = total_views / len(videos) if videos else 0
        avg_likes = total_likes / len(videos) if videos else 0
        avg_comments = total_comments / len(videos) if videos else 0
        
        # Engagement rate analysis
        engagement_rates = [v.get('engagement_rate', 0) or 0 for v in videos]
        avg_engagement = sum(engagement_rates) / len(engagement_rates) if engagement_rates else 0
        
        # Quality score analysis
        quality_scores = [v.get('quality_score', 0) for v in videos]
        avg_quality = sum(quality_scores) / len(quality_scores) if quality_scores else 0
        
        # Channel analysis
        channels = {}
        for video in videos:
            channel = video.get('channel_title', 'Unknown')
            if channel not in channels:
                channels[channel] = {'count': 0, 'total_views': 0}
            channels[channel]['count'] += 1
            channels[channel]['total_views'] += video.get('view_count', 0)
        
        top_channels = sorted(
            channels.items(), 
            key=lambda x: x[1]['total_views'], 
            reverse=True
        )[:5]
        
        return {
            'summary': {
                'total_videos': len(videos),
                'total_views': total_views,
                'total_likes': total_likes,
                'total_comments': total_comments,
                'average_views': round(avg_views, 2),
                'average_likes': round(avg_likes, 2),
                'average_comments': round(avg_comments, 2),
                'average_engagement_rate': round(avg_engagement, 4),
                'average_quality_score': round(avg_quality, 3)
            },
            'top_channels': [
                {
                    'channel': channel,
                    'video_count': data['count'],
                    'total_views': data['total_views']
                }
                for channel, data in top_channels
            ]
        }
    
    async def _export_json(self, data: Dict[str, Any]) -> bytes:
        """Export data as JSON."""
        json_str = json.dumps(data, indent=2, ensure_ascii=False)
        return json_str.encode('utf-8')
    
    async def _export_csv(self, data: Dict[str, Any]) -> bytes:
        """Export data as CSV."""
        output = io.StringIO()
        
        if not data.get('videos'):
            output.write("No video data to export\n")
            return output.getvalue().encode('utf-8')
        
        # Get all possible field names
        fieldnames = set()
        for video in data['videos']:
            fieldnames.update(video.keys())
        
        # Convert tags list to string for CSV
        for video in data['videos']:
            if 'tags' in video and isinstance(video['tags'], list):
                video['tags'] = ', '.join(video['tags'])
        
        fieldnames = sorted(list(fieldnames))
        
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()
        
        for video in data['videos']:
            writer.writerow(video)
        
        return output.getvalue().encode('utf-8')
    
    async def _export_xlsx(self, data: Dict[str, Any]) -> bytes:
        """Export data as Excel file."""
        if not EXPORT_DEPENDENCIES_AVAILABLE:
            raise ValueError("Excel export requires openpyxl and pandas")
        
        output = io.BytesIO()
        
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            # Videos sheet
            if data.get('videos'):
                videos_df = pd.DataFrame(data['videos'])
                
                # Convert tags list to string
                if 'tags' in videos_df.columns:
                    videos_df['tags'] = videos_df['tags'].apply(
                        lambda x: ', '.join(x) if isinstance(x, list) else str(x)
                    )
                
                videos_df.to_excel(writer, sheet_name='Videos', index=False)
            
            # Metadata sheet
            if data.get('query_metadata'):
                metadata_items = []
                for key, value in data['query_metadata'].items():
                    if isinstance(value, list):
                        value = ', '.join(map(str, value))
                    metadata_items.append({'Property': key, 'Value': str(value)})
                
                metadata_df = pd.DataFrame(metadata_items)
                metadata_df.to_excel(writer, sheet_name='Query Info', index=False)
            
            # Analytics sheet
            if data.get('analytics'):
                analytics = data['analytics']
                
                # Summary data
                if analytics.get('summary'):
                    summary_items = []
                    for key, value in analytics['summary'].items():
                        summary_items.append({'Metric': key, 'Value': value})
                    
                    summary_df = pd.DataFrame(summary_items)
                    summary_df.to_excel(writer, sheet_name='Analytics Summary', index=False)
                
                # Top channels
                if analytics.get('top_channels'):
                    channels_df = pd.DataFrame(analytics['top_channels'])
                    channels_df.to_excel(writer, sheet_name='Top Channels', index=False)
        
        output.seek(0)
        return output.read()
    
    async def _export_pdf(self, data: Dict[str, Any]) -> bytes:
        """Export data as PDF report."""
        if not EXPORT_DEPENDENCIES_AVAILABLE:
            raise ValueError("PDF export requires reportlab")
        
        output = io.BytesIO()
        doc = SimpleDocTemplate(output, pagesize=A4)
        story = []
        
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=16,
            spaceAfter=30,
            textColor=colors.darkblue
        )
        
        # Title
        story.append(Paragraph("YouTube Content Search Results", title_style))
        story.append(Spacer(1, 12))
        
        # Export info
        export_info = data.get('export_info', {})
        info_text = f"""
        <b>Export Date:</b> {export_info.get('exported_at', 'Unknown')}<br/>
        <b>Total Videos:</b> {export_info.get('total_videos', 0)}<br/>
        <b>Search Time:</b> {export_info.get('search_time_ms', 0)} ms<br/>
        <b>API Quota Used:</b> {export_info.get('quota_used', 0)}
        """
        story.append(Paragraph(info_text, styles['Normal']))
        story.append(Spacer(1, 20))
        
        # Query metadata
        if data.get('query_metadata'):
            story.append(Paragraph("Search Query Information", styles['Heading2']))
            
            query_info = data['query_metadata']
            query_text = f"""
            <b>Original Idea:</b> {query_info.get('original_idea', 'N/A')}<br/>
            <b>Intent:</b> {query_info.get('intent', 'N/A')}<br/>
            <b>Confidence:</b> {query_info.get('confidence', 0):.2%}<br/>
            <b>Keywords:</b> {', '.join(query_info.get('processed_keywords', []))}
            """
            story.append(Paragraph(query_text, styles['Normal']))
            story.append(Spacer(1, 20))
        
        # Videos table
        if data.get('videos'):
            story.append(Paragraph("Top Search Results", styles['Heading2']))
            
            # Prepare table data (limit to top 20 for PDF)
            videos = data['videos'][:20]
            table_data = [['Rank', 'Title', 'Channel', 'Views', 'Relevance']]
            
            for i, video in enumerate(videos, 1):
                title = video.get('title', 'N/A')
                if len(title) > 50:
                    title = title[:50] + "..."
                
                channel = video.get('channel_title', 'N/A')
                if len(channel) > 30:
                    channel = channel[:30] + "..."
                
                views = self._format_number(video.get('view_count', 0))
                relevance = f"{video.get('relevance_score', 0):.2%}"
                
                table_data.append([str(i), title, channel, views, relevance])
            
            table = Table(table_data, colWidths=[0.5*inch, 3*inch, 2*inch, 1*inch, 1*inch])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('FONTSIZE', (0, 1), (-1, -1), 8),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            story.append(table)
        
        # Analytics summary
        if data.get('analytics', {}).get('summary'):
            story.append(Spacer(1, 20))
            story.append(Paragraph("Analytics Summary", styles['Heading2']))
            
            summary = data['analytics']['summary']
            analytics_text = f"""
            <b>Total Videos:</b> {summary.get('total_videos', 0)}<br/>
            <b>Average Views:</b> {self._format_number(summary.get('average_views', 0))}<br/>
            <b>Average Engagement Rate:</b> {summary.get('average_engagement_rate', 0):.2%}<br/>
            <b>Average Quality Score:</b> {summary.get('average_quality_score', 0):.2f}/1.0
            """
            story.append(Paragraph(analytics_text, styles['Normal']))
        
        # Build PDF
        doc.build(story)
        output.seek(0)
        return output.read()
    
    def _format_number(self, num: int) -> str:
        """Format number for display."""
        if num >= 1000000:
            return f"{num/1000000:.1f}M"
        elif num >= 1000:
            return f"{num/1000:.1f}K"
        else:
            return str(num)
    
    async def export_analytics_report(
        self,
        analytics_data: Dict[str, Any],
        export_format: str = 'json'
    ) -> bytes:
        """Export analytics report in specified format."""
        if export_format not in self.supported_formats:
            raise ValueError(f"Unsupported export format: {export_format}")
        
        # Prepare analytics export data
        export_data = {
            'report_info': {
                'generated_at': datetime.now().isoformat(),
                'report_type': 'analytics_summary'
            },
            'analytics': analytics_data
        }
        
        # Export based on format
        if export_format == 'json':
            return await self._export_json(export_data)
        elif export_format == 'csv':
            return await self._export_analytics_csv(analytics_data)
        elif export_format == 'xlsx':
            return await self._export_analytics_xlsx(analytics_data)
        elif export_format == 'pdf':
            return await self._export_analytics_pdf(analytics_data)
    
    async def _export_analytics_csv(self, analytics_data: Dict[str, Any]) -> bytes:
        """Export analytics as CSV."""
        output = io.StringIO()
        
        # Write different sections
        if analytics_data.get('trends'):
            output.write("Trend Analysis\n")
            writer = csv.DictWriter(output, fieldnames=['keyword', 'trend_score', 'search_volume', 'competition_level'])
            writer.writeheader()
            for trend in analytics_data['trends']:
                writer.writerow(trend)
            output.write("\n")
        
        if analytics_data.get('content_insights'):
            output.write("Content Insights\n")
            insights = analytics_data['content_insights']
            output.write(f"Topic: {insights.get('topic', 'N/A')}\n")
            output.write(f"Total Videos: {insights.get('total_videos', 0)}\n")
            output.write(f"Average Views: {insights.get('avg_view_count', 0)}\n")
            output.write(f"Average Engagement: {insights.get('avg_engagement_rate', 0)}\n")
            output.write("\n")
        
        return output.getvalue().encode('utf-8')
    
    async def _export_analytics_xlsx(self, analytics_data: Dict[str, Any]) -> bytes:
        """Export analytics as Excel file."""
        if not EXPORT_DEPENDENCIES_AVAILABLE:
            raise ValueError("Excel export requires openpyxl and pandas")
        
        output = io.BytesIO()
        
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            # Trends sheet
            if analytics_data.get('trends'):
                trends_df = pd.DataFrame(analytics_data['trends'])
                trends_df.to_excel(writer, sheet_name='Trends', index=False)
            
            # Content insights
            if analytics_data.get('content_insights'):
                insights = analytics_data['content_insights']
                
                # Summary data
                summary_data = []
                for key, value in insights.items():
                    if not isinstance(value, (list, dict)):
                        summary_data.append({'Metric': key, 'Value': value})
                
                if summary_data:
                    summary_df = pd.DataFrame(summary_data)
                    summary_df.to_excel(writer, sheet_name='Content Insights', index=False)
                
                # Top creators
                if insights.get('top_creators'):
                    creators_df = pd.DataFrame(insights['top_creators'])
                    creators_df.to_excel(writer, sheet_name='Top Creators', index=False)
        
        output.seek(0)
        return output.read()
    
    async def _export_analytics_pdf(self, analytics_data: Dict[str, Any]) -> bytes:
        """Export analytics as PDF report."""
        if not EXPORT_DEPENDENCIES_AVAILABLE:
            raise ValueError("PDF export requires reportlab")
        
        output = io.BytesIO()
        doc = SimpleDocTemplate(output, pagesize=A4)
        story = []
        
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=16,
            spaceAfter=30,
            textColor=colors.darkblue
        )
        
        # Title
        story.append(Paragraph("YouTube Content Analytics Report", title_style))
        story.append(Spacer(1, 12))
        
        # Report info
        story.append(Paragraph(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", styles['Normal']))
        story.append(Spacer(1, 20))
        
        # Trends section
        if analytics_data.get('trends'):
            story.append(Paragraph("Trend Analysis", styles['Heading2']))
            
            trends_data = [['Keyword', 'Trend Score', 'Search Volume', 'Competition']]
            for trend in analytics_data['trends'][:10]:  # Top 10
                trends_data.append([
                    trend.get('keyword', 'N/A'),
                    f"{trend.get('trend_score', 0):.2f}",
                    str(trend.get('search_volume', 0)),
                    trend.get('competition_level', 'N/A')
                ])
            
            trends_table = Table(trends_data, colWidths=[2*inch, 1*inch, 1*inch, 1*inch])
            trends_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('FONTSIZE', (0, 1), (-1, -1), 8),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            story.append(trends_table)
            story.append(Spacer(1, 20))
        
        # Content insights section
        if analytics_data.get('content_insights'):
            story.append(Paragraph("Content Insights", styles['Heading2']))
            
            insights = analytics_data['content_insights']
            insights_text = f"""
            <b>Topic:</b> {insights.get('topic', 'N/A')}<br/>
            <b>Total Videos Analyzed:</b> {insights.get('total_videos', 0)}<br/>
            <b>Average View Count:</b> {self._format_number(insights.get('avg_view_count', 0))}<br/>
            <b>Average Engagement Rate:</b> {insights.get('avg_engagement_rate', 0):.2%}
            """
            story.append(Paragraph(insights_text, styles['Normal']))
        
        # Build PDF
        doc.build(story)
        output.seek(0)
        return output.read()
    
    def get_supported_formats(self) -> List[str]:
        """Get list of supported export formats."""
        return self.supported_formats.copy()


# Global export manager instance
export_manager = ExportManager()


def get_export_manager() -> ExportManager:
    """Get export manager instance."""
    return export_manager