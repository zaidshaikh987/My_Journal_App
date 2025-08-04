/**
 * calendar.js - Handles all calendar-related functionality
 * for the Journal Calendar application
 */

class JournalCalendar {
    constructor() {
        this.calendarCells = document.querySelectorAll('td[data-entry-url]');
        this.navMonth = document.querySelector('.calendar-nav-month');
        this.navYear = document.querySelector('.calendar-nav-year');
        this.prevMonthBtn = document.querySelector('.prev-month');
        this.nextMonthBtn = document.querySelector('.next-month');
        this.todayBtn = document.querySelector('.today-btn');
        this.calendarBody = document.querySelector('.calendar-body');
        
        this.init();
    }
    
    init() {
        // Add event listeners
        this.addEventListeners();
        
        // Initialize tooltips
        this.initTooltips();
        
        // Highlight today's date
        this.highlightToday();
    }
    
    addEventListeners() {
        // Calendar cell clicks
        this.calendarCells.forEach(cell => {
            cell.addEventListener('click', (e) => {
                // Don't navigate if clicking on a button inside the cell
                if (e.target.tagName === 'BUTTON' || e.target.closest('button')) {
                    return;
                }
                window.location.href = cell.getAttribute('data-entry-url');
            });
            
            // Add hover effect
            cell.addEventListener('mouseenter', () => {
                if (!cell.classList.contains('table-active')) {
                    cell.classList.add('table-hover');
                }
            });
            
            cell.addEventListener('mouseleave', () => {
                cell.classList.remove('table-hover');
            });
        });
        
        // Navigation buttons
        if (this.prevMonthBtn) {
            this.prevMonthBtn.addEventListener('click', () => this.navigateMonth(-1));
        }
        
        if (this.nextMonthBtn) {
            this.nextMonthBtn.addEventListener('click', () => this.navigateMonth(1));
        }
        
        if (this.todayBtn) {
            this.todayBtn.addEventListener('click', () => this.goToToday());
        }
        
        // Keyboard navigation
        document.addEventListener('keydown', (e) => {
            if (e.key === 'ArrowLeft') {
                this.navigateMonth(-1);
            } else if (e.key === 'ArrowRight') {
                this.navigateMonth(1);
            } else if (e.key === 't' || e.key === 'T') {
                this.goToToday();
            }
        });
    }
    
    initTooltips() {
        // Initialize Bootstrap tooltips
        const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
        tooltipTriggerList.map(function (tooltipTriggerEl) {
            return new bootstrap.Tooltip(tooltipTriggerEl);
        });
    }
    
    highlightToday() {
        const today = new Date();
        const todayCell = Array.from(this.calendarCells).find(cell => {
            const cellDate = new Date(cell.getAttribute('data-date'));
            return cellDate.toDateString() === today.toDateString();
        });
        
        if (todayCell) {
            todayCell.classList.add('today-highlight');
            
            // Smooth scroll to today's cell if it's not in view
            setTimeout(() => {
                todayCell.scrollIntoView({
                    behavior: 'smooth',
                    block: 'center',
                    inline: 'center'
                });
            }, 500);
        }
    }
    
    navigateMonth(direction) {
        const currentUrl = new URL(window.location.href);
        let year = parseInt(currentUrl.searchParams.get('year') || new Date().getFullYear());
        let month = parseInt(currentUrl.searchParams.get('month') || (new Date().getMonth() + 1));
        
        // Calculate new month and year
        let newMonth = month + direction;
        let newYear = year;
        
        if (newMonth > 12) {
            newMonth = 1;
            newYear++;
        } else if (newMonth < 1) {
            newMonth = 12;
            newYear--;
        }
        
        // Update URL with new month/year
        currentUrl.searchParams.set('year', newYear);
        currentUrl.searchParams.set('month', newMonth);
        window.location.href = currentUrl.toString();
    }
    
    goToToday() {
        const currentUrl = new URL(window.location.href);
        const today = new Date();
        
        // Remove month and year params to go to current month
        currentUrl.searchParams.delete('year');
        currentUrl.searchParams.delete('month');
        
        window.location.href = currentUrl.toString();
    }
}

// Initialize the calendar when the DOM is fully loaded
document.addEventListener('DOMContentLoaded', () => {
    // Only initialize if we're on a page with a calendar
    if (document.querySelector('.calendar-table')) {
        window.journalCalendar = new JournalCalendar();
    }
});
