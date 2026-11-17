"""
ByteTrack Multi-Object Tracking Wrapper and Track Telemetry.
Tracks detected road objects across sequential frames, preserving unique track IDs
and estimating velocity / trajectory persistence.
"""

from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from collections import defaultdict, deque
import numpy as np
import logging

logger = logging.getLogger(__name__)


class RoadTracker:
    """
    ByteTrack multi-object tracker manager for autonomous road vision.
    Maintains persistent track state, position histories, and velocity vectors.
    """
    def __init__(
        self,
        tracker_type: str = "bytetrack",
        history_len: int = 30,
    ):
        self.tracker_type = tracker_type
        self.history_len = history_len
        # track_id -> deque of (frame_idx, center_x, center_y, box_w, box_h)
        self.track_histories = defaultdict(lambda: deque(maxlen=self.history_len))
        self.track_classes = {}
        self.track_first_frame = {}
        self.track_last_frame = {}
        self.total_id_switches = 0
        self.current_frame_idx = 0

    def reset(self):
        """Resets tracker internal state for a new video sequence."""
        self.track_histories.clear()
        self.track_classes.clear()
        self.track_first_frame.clear()
        self.track_last_frame.clear()
        self.current_frame_idx = 0

    def update_tracks(
        self,
        detections: List[Dict[str, Any]],
        frame_idx: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Updates tracking history with new frame detections.
        detections: list of dicts with keys: 'bbox', 'confidence', 'class_id', 'track_id' (if assigned by YOLO.track)
        Returns enriched detections with 'track_age', 'trajectory', and 'estimated_speed_px'.
        """
        if frame_idx is None:
            self.current_frame_idx += 1
            frame_idx = self.current_frame_idx
        else:
            self.current_frame_idx = frame_idx

        enriched = []
        for det in detections:
            tid = det.get("track_id")
            if tid is None:
                enriched.append(det)
                continue

            tid = int(tid)
            bbox = det.get("bbox", [0, 0, 0, 0])
            x1, y1, x2, y2 = bbox
            cx = (x1 + x2) / 2.0
            cy = (y1 + y2) / 2.0
            bw = x2 - x1
            bh = y2 - y1

            if tid not in self.track_first_frame:
                self.track_first_frame[tid] = frame_idx
            self.track_last_frame[tid] = frame_idx
            self.track_classes[tid] = det.get("class_id", 0)

            history = self.track_histories[tid]
            history.append((frame_idx, cx, cy, bw, bh))

            track_age = frame_idx - self.track_first_frame[tid] + 1

            # Estimate pixel velocity
            speed_px_per_frame = 0.0
            if len(history) >= 2:
                prev = history[-2]
                dx = cx - prev[1]
                dy = cy - prev[2]
                df = max(1, frame_idx - prev[0])
                speed_px_per_frame = np.sqrt(dx**2 + dy**2) / df

            item = dict(det)
            item["track_id"] = tid
            item["track_age"] = track_age
            item["speed_px"] = round(float(speed_px_per_frame), 2)
            item["is_persistent"] = (track_age >= 3)
            enriched.append(item)

        return enriched

    def get_track_summary(self) -> Dict[str, Any]:
        """
        Returns track statistics over the processed sequence.
        """
        total_unique_tracks = len(self.track_first_frame)
        lifespans = [
            (self.track_last_frame[tid] - self.track_first_frame[tid] + 1)
            for tid in self.track_first_frame
        ]

        mean_lifespan = float(np.mean(lifespans)) if lifespans else 0.0
        max_lifespan = int(np.max(lifespans)) if lifespans else 0

        return {
            "total_unique_tracks": total_unique_tracks,
            "mean_track_lifespan_frames": round(mean_lifespan, 2),
            "max_track_lifespan_frames": max_lifespan,
            "total_frames_processed": self.current_frame_idx,
        }
