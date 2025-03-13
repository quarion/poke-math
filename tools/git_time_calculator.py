#!/usr/bin/env python
# -*- coding: utf-8 -*-

import argparse
import subprocess
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import List, Tuple

# Default configuration values
DEFAULT_BREAK_THRESHOLD_MINUTES = 90
DEFAULT_PRE_COMMIT_BUFFER_MINUTES = 30

@dataclass
class WorkBlock:
    start: datetime
    end: datetime
    
    @property
    def duration_minutes(self) -> float:
        return (self.end - self.start).total_seconds() / 60

@dataclass
class DayWorkSummary:
    date: str
    blocks: List[WorkBlock]
    breaks: List[Tuple[datetime, datetime]]
    
    @property
    def total_minutes(self) -> float:
        return sum(block.duration_minutes for block in self.blocks)
    
    @property
    def total_break_minutes(self) -> float:
        return sum((end - start).total_seconds() / 60 for start, end in self.breaks)

def get_git_log():
    """Retrieve git log with commit timestamps"""
    command = ['git', 'log', '--pretty=format:%aI|%an']
    result = subprocess.run(command, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Error running git command: {result.stderr}")
        return []
    
    return result.stdout.strip().split('\n')

def parse_git_log(log_entries):
    """Parse git log entries and organize commits by day"""
    commits_by_day = defaultdict(list)
    
    for entry in log_entries:
        try:
            timestamp_str, author = entry.split('|', 1)
            timestamp = datetime.fromisoformat(timestamp_str)
            day = timestamp.date().isoformat()
            commits_by_day[day].append(timestamp)
        except (ValueError, IndexError) as e:
            print(f"Error parsing log entry '{entry}': {e}")
            continue
    
    return commits_by_day

def calculate_work_time(commits_by_day, break_threshold_minutes, pre_commit_buffer_minutes):
    """Calculate work time for each day, accounting for breaks between commits"""
    daily_summaries = {}
    total_minutes = 0
    
    for day, timestamps in commits_by_day.items():
        # Sort timestamps
        sorted_timestamps = sorted(timestamps)
        
        # Initialize with the first work block
        current_block_start = sorted_timestamps[0] - timedelta(minutes=pre_commit_buffer_minutes)
        current_block_end = sorted_timestamps[0]
        
        work_blocks = []
        breaks = []
        
        # Process all commits to identify work blocks and breaks
        for i in range(1, len(sorted_timestamps)):
            time_diff = (sorted_timestamps[i] - sorted_timestamps[i-1]).total_seconds() / 60
            
            if time_diff > break_threshold_minutes:
                # Finish the current block
                work_blocks.append(WorkBlock(current_block_start, current_block_end))
                
                # Record the break - must end pre_commit_buffer_minutes before next commit
                # to avoid overlap with next work session
                break_start = sorted_timestamps[i-1]
                break_end = sorted_timestamps[i] - timedelta(minutes=pre_commit_buffer_minutes)
                
                # Ensure break has positive duration
                if break_end > break_start:
                    breaks.append((break_start, break_end))
                
                # Start a new block with pre-commit buffer
                current_block_start = sorted_timestamps[i] - timedelta(minutes=pre_commit_buffer_minutes)
                current_block_end = sorted_timestamps[i]
            else:
                # Extend the current block
                current_block_end = sorted_timestamps[i]
        
        # Add the final block
        work_blocks.append(WorkBlock(current_block_start, current_block_end))
        
        # Create the day summary
        daily_summaries[day] = DayWorkSummary(date=day, blocks=work_blocks, breaks=breaks)
        
        # Add to total work time
        total_minutes += daily_summaries[day].total_minutes
    
    return daily_summaries, total_minutes

def format_time(minutes):
    """Format minutes as hours and minutes"""
    hours = int(minutes // 60)
    remaining_minutes = int(minutes % 60)
    return f"{hours}h {remaining_minutes}m"

def format_datetime(dt):
    """Format datetime for display"""
    return dt.strftime('%H:%M')

def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description="Calculate work time based on git commit history",
        epilog="""
Examples:
  # Use default settings
  python tools/git_time_calculator.py
  
  # Set break threshold to 45 minutes
  python tools/git_time_calculator.py --break-threshold 45
  
  # Set pre-commit buffer to 15 minutes and break threshold to 40 minutes
  python tools/git_time_calculator.py --pre-commit-buffer 15 --break-threshold 40
""",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        "--break-threshold", 
        type=int,
        default=DEFAULT_BREAK_THRESHOLD_MINUTES,
        help=f"Minutes between commits that constitute a break (default: {DEFAULT_BREAK_THRESHOLD_MINUTES})"
    )
    
    parser.add_argument(
        "--pre-commit-buffer",
        type=int,
        default=DEFAULT_PRE_COMMIT_BUFFER_MINUTES,
        help=f"Minutes of work before first commit in a session (default: {DEFAULT_PRE_COMMIT_BUFFER_MINUTES})"
    )
    
    return parser.parse_args()

def main():
    args = parse_arguments()
    
    print("Analyzing git log to calculate work time...")
    print(f"Using break threshold: {args.break_threshold} minutes")
    print(f"Using pre-commit buffer: {args.pre_commit_buffer} minutes")
    
    log_entries = get_git_log()
    
    if not log_entries:
        print("No git log entries found.")
        return
    
    commits_by_day = parse_git_log(log_entries)
    daily_summaries, total_minutes = calculate_work_time(
        commits_by_day, 
        args.break_threshold, 
        args.pre_commit_buffer
    )
    
    print("\n📊 WORK TIME BREAKDOWN BY DAY")
    print("=" * 80)
    
    for day, summary in sorted(daily_summaries.items()):
        day_total = format_time(summary.total_minutes)
        print(f"\n📅 {day} - Total work time: {day_total}")
        
        print("\n  🔄 Work Sessions:")
        print("  " + "-" * 76)
        print("  |  Start  |   End   | Duration |                                           |")
        print("  " + "-" * 76)
        
        for i, block in enumerate(summary.blocks, 1):
            start_time = format_datetime(block.start)
            end_time = format_datetime(block.end)
            duration = format_time(block.duration_minutes)
            print(f"  | {start_time} | {end_time} | {duration:^8} | Session {i:<38} |")
        
        print("  " + "-" * 76)
        
        if summary.breaks:
            print("\n  ⏸️  Breaks:")
            print("  " + "-" * 76)
            print("  |  Start  |   End   | Duration |                                           |")
            print("  " + "-" * 76)
            
            for i, (break_start, break_end) in enumerate(summary.breaks, 1):
                start_time = format_datetime(break_start)
                end_time = format_datetime(break_end)
                duration = format_time((break_end - break_start).total_seconds() / 60)
                print(f"  | {start_time} | {end_time} | {duration:^8} | Break {i:<39} |")
            
            print("  " + "-" * 76)
        
        print()
    
    print("=" * 80)
    print(f"⏱️  Total time spent on the project: {format_time(total_minutes)}")
    print("=" * 80)

if __name__ == "__main__":
    main() 