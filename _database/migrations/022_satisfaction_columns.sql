-- Migration 022: Add dislikes column to yt_video_metrics for satisfaction analysis (Call 2)
-- likes and subscribers_gained columns already exist in yt_video_metrics

ALTER TABLE yt_video_metrics ADD COLUMN IF NOT EXISTS dislikes INTEGER DEFAULT 0;
