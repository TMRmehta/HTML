/**
 * Utility functions for date formatting and grouping
 */

export interface DateGroup {
    date: string;
    displayDate: string;
    messages: any[];
  }
  
  /**
   * Formats a timestamp to show relative date information
   * @param date - The date to format
   * @returns Formatted date string (Today, Yesterday, or actual date)
   */
  export function formatRelativeDate(date: Date): string {
    const now = new Date();
    const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
    const yesterday = new Date(today);
    yesterday.setDate(yesterday.getDate() - 1);
    
    const messageDate = new Date(date.getFullYear(), date.getMonth(), date.getDate());
    
    if (messageDate.getTime() === today.getTime()) {
      return 'Today';
    } else if (messageDate.getTime() === yesterday.getTime()) {
      return 'Yesterday';
    } else {
      return new Intl.DateTimeFormat('en-US', {
        weekday: 'long',
        year: 'numeric',
        month: 'long',
        day: 'numeric'
      }).format(date);
    }
  }
  
  /**
   * Formats a timestamp to show time only
   * @param date - The date to format
   * @returns Formatted time string
   */
  export function formatTime(date: Date): string {
    return new Intl.DateTimeFormat('en-US', {
      hour: '2-digit',
      minute: '2-digit',
      hour12: true
    }).format(date);
  }
  
  /**
   * Formats a timestamp to show both date and time
   * @param date - The date to format
   * @returns Formatted date and time string
   */
  export function formatDateTime(date: Date): string {
    const relativeDate = formatRelativeDate(date);
    const time = formatTime(date);
    
    if (relativeDate === 'Today' || relativeDate === 'Yesterday') {
      return `${relativeDate} at ${time}`;
    } else {
      return `${relativeDate} at ${time}`;
    }
  }
  
  /**
   * Groups messages by date for display
   * @param messages - Array of messages with timestamp property
   * @returns Array of date groups with messages (dates newest first, messages oldest first within each group)
   */
  export function groupMessagesByDate(messages: any[]): DateGroup[] {
    const groups = new Map<string, DateGroup>();
    
    messages.forEach(message => {
      const date = new Date(message.timestamp);
      const dateKey = new Date(date.getFullYear(), date.getMonth(), date.getDate()).toISOString();
      
      if (!groups.has(dateKey)) {
        groups.set(dateKey, {
          date: dateKey,
          displayDate: formatRelativeDate(date),
          messages: []
        });
      }
      
      groups.get(dateKey)!.messages.push(message);
    });
    
     // Sort groups by date (oldest first - Today at bottom)
     return Array.from(groups.values())
       .sort((a, b) => {
         const now = new Date();
         const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
         const yesterday = new Date(today);
         yesterday.setDate(yesterday.getDate() - 1);
         
         const dateA = new Date(a.date);
         const dateB = new Date(b.date);
         
         // Check if dates are Today or Yesterday
         const isTodayA = dateA.getTime() === today.getTime();
         const isTodayB = dateB.getTime() === today.getTime();
         const isYesterdayA = dateA.getTime() === yesterday.getTime();
         const isYesterdayB = dateB.getTime() === yesterday.getTime();
         
         // Today comes last (at bottom)
         if (isTodayA && !isTodayB) return 1;
         if (!isTodayA && isTodayB) return -1;
         
         // Yesterday comes second to last
         if (isYesterdayA && !isYesterdayB && !isTodayB) return 1;
         if (!isYesterdayA && isYesterdayB && !isTodayA) return -1;
         
         // For other dates, sort oldest first
         return dateA.getTime() - dateB.getTime();
       })
      .map(group => ({
        ...group,
        // Sort messages within each group from oldest to newest (chronological order)
        messages: group.messages.sort((a, b) => 
          new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime()
        )
      }));
  }
  
  /**
   * Formats time for display within date groups
   * @param date - The date to format
   * @returns Formatted time string (e.g., "2:30 PM")
   */
  export function formatTimeOnly(date: Date): string {
    return new Intl.DateTimeFormat('en-US', {
      hour: '2-digit',
      minute: '2-digit',
      hour12: true
    }).format(date);
  }
  
  /**
   * Formats a compact time for message display
   * @param date - The date to format
   * @returns Compact time string (e.g., "2:30 PM" or "14:30")
   */
  export function formatCompactTime(date: Date): string {
    return new Intl.DateTimeFormat('en-US', {
      hour: 'numeric',
      minute: '2-digit',
      hour12: true
    }).format(date);
  }
  
  /**
   * Checks if two messages are close in time (within 5 minutes)
   * @param msg1 - First message
   * @param msg2 - Second message
   * @returns True if messages are close in time
   */
  export function areMessagesCloseInTime(msg1: any, msg2: any): boolean {
    const time1 = new Date(msg1.timestamp).getTime();
    const time2 = new Date(msg2.timestamp).getTime();
    const diffInMinutes = Math.abs(time1 - time2) / (1000 * 60);
    return diffInMinutes <= 5;
  }
  
  /**
   * Groups messages by date and time proximity for better display
   * @param messages - Array of messages with timestamp property
   * @returns Array of date groups with time-grouped messages (dates newest first, messages oldest first within each group)
   */
  export function groupMessagesByDateAndTime(messages: any[]): DateGroup[] {
    const groups = new Map<string, DateGroup>();
    
    messages.forEach(message => {
      const date = new Date(message.timestamp);
      const dateKey = new Date(date.getFullYear(), date.getMonth(), date.getDate()).toISOString();
      
      if (!groups.has(dateKey)) {
        groups.set(dateKey, {
          date: dateKey,
          displayDate: formatRelativeDate(date),
          messages: []
        });
      }
      
      groups.get(dateKey)!.messages.push(message);
    });
    
    // Sort groups by date (newest first) and messages within each group by time (oldest first)
    return Array.from(groups.values())
      .sort((a, b) => new Date(b.date).getTime() - new Date(a.date).getTime())
      .map(group => ({
        ...group,
        // Sort messages within each group from oldest to newest (chronological order)
        messages: group.messages.sort((a, b) => 
          new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime()
        )
      }));
  }
  
  /**
   * Checks if two dates are on the same day
   * @param date1 - First date
   * @param date2 - Second date
   * @returns True if both dates are on the same day
   */
  export function isSameDay(date1: Date, date2: Date): boolean {
    return date1.getFullYear() === date2.getFullYear() &&
           date1.getMonth() === date2.getMonth() &&
           date1.getDate() === date2.getDate();
  }
  
  /**
   * Gets a short date format for chat list items
   * @param date - The date to format
   * @returns Short formatted date string
   */
  export function formatShortDate(date: Date): string {
    const now = new Date();
    const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
    const yesterday = new Date(today);
    yesterday.setDate(yesterday.getDate() - 1);
    
    const messageDate = new Date(date.getFullYear(), date.getMonth(), date.getDate());
    
    if (messageDate.getTime() === today.getTime()) {
      return 'Today';
    } else if (messageDate.getTime() === yesterday.getTime()) {
      return 'Yesterday';
    } else {
      const diffInDays = Math.floor((today.getTime() - messageDate.getTime()) / (1000 * 60 * 60 * 24));
      
      if (diffInDays < 7) {
        return new Intl.DateTimeFormat('en-US', {
          weekday: 'short'
        }).format(date);
      } else if (diffInDays < 365) {
        return new Intl.DateTimeFormat('en-US', {
          month: 'short',
          day: 'numeric'
        }).format(date);
      } else {
        return new Intl.DateTimeFormat('en-US', {
          month: 'short',
          day: 'numeric',
          year: '2-digit'
        }).format(date);
      }
    }
  }
  
  /**
   * Sorts chat histories by timestamp with proper date handling
   * @param chats - Array of chat objects with timestamp property
   * @returns Sorted array (newest first)
   */
  export function sortChatsByDate(chats: any[]): any[] {
    return chats.sort((a, b) => {
      const dateA = new Date(a.timestamp);
      const dateB = new Date(b.timestamp);
      
      // Sort by timestamp (newest first)
      return dateB.getTime() - dateA.getTime();
    });
  }
  
  /**
   * Groups and sorts chat histories by relative date
   * @param chats - Array of chat objects with timestamp property
   * @returns Object with grouped chats (all groups sorted newest first)
   */
  export function groupChatsByRelativeDate(chats: any[]): { today: any[], yesterday: any[], older: any[] } {
    const now = new Date();
    const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
    const yesterday = new Date(today);
    yesterday.setDate(yesterday.getDate() - 1);
    
    const grouped = {
      today: [] as any[],
      yesterday: [] as any[],
      older: [] as any[]
    };
    
    chats.forEach(chat => {
      const chatDate = new Date(chat.timestamp);
      const messageDate = new Date(chatDate.getFullYear(), chatDate.getMonth(), chatDate.getDate());
      
      if (messageDate.getTime() === today.getTime()) {
        grouped.today.push(chat);
      } else if (messageDate.getTime() === yesterday.getTime()) {
        grouped.yesterday.push(chat);
      } else {
        grouped.older.push(chat);
      }
    });
    
    // Sort each group by timestamp (newest first)
    grouped.today.sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime());
    grouped.yesterday.sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime());
    grouped.older.sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime());
    
    return grouped;
  }
  
  /**
   * Groups chats by date with proper formatting for display
   * @param chats - Array of chat objects with timestamp property
   * @returns Array of date groups with chats (dates newest first, chats newest first within each group)
   */
  export function groupChatsForDisplay(chats: any[]): Array<{ date: string, displayDate: string, chats: any[] }> {
    const now = new Date();
    const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
    const yesterday = new Date(today);
    yesterday.setDate(yesterday.getDate() - 1);
    
    const groups = new Map<string, { date: string, displayDate: string, chats: any[] }>();
    
    chats.forEach(chat => {
      const chatDate = new Date(chat.timestamp);
      const messageDate = new Date(chatDate.getFullYear(), chatDate.getMonth(), chatDate.getDate());
      
      let dateKey: string;
      let displayDate: string;
      
      if (messageDate.getTime() === today.getTime()) {
        dateKey = 'today';
        displayDate = 'Today';
      } else if (messageDate.getTime() === yesterday.getTime()) {
        dateKey = 'yesterday';
        displayDate = 'Yesterday';
      } else {
        dateKey = messageDate.toISOString().split('T')[0];
        displayDate = new Intl.DateTimeFormat('en-US', {
          weekday: 'long',
          year: 'numeric',
          month: 'long',
          day: 'numeric'
        }).format(messageDate);
      }
      
      if (!groups.has(dateKey)) {
        groups.set(dateKey, {
          date: dateKey,
          displayDate,
          chats: []
        });
      }
      
      groups.get(dateKey)!.chats.push(chat);
    });
    
    // Sort groups by date (newest first - today at top)
    const sortedGroups = Array.from(groups.values()).sort((a, b) => {
      if (a.date === 'today') return -1;
      if (b.date === 'today') return 1;
      if (a.date === 'yesterday') return -1;
      if (b.date === 'yesterday') return 1;
      return new Date(b.date).getTime() - new Date(a.date).getTime();
    });
    
     // Sort chats within each group by timestamp (newest first - newest at top of each group)
     return sortedGroups.map(group => ({
       ...group,
       chats: group.chats.sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime())
     }));
  }