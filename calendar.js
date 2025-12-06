document.addEventListener('DOMContentLoaded', function() {
    var calendarEl = document.getElementById('calendar');
    var calendar = new FullCalendar.Calendar(calendarEl, {
      initialView: 'dayGridMonth',
      events: '/api/events',
      headerToolbar: { left: 'prev,next today', center: 'title', right: 'dayGridMonth,timeGridWeek' },
      eventDidMount: function(info) {
        info.el.setAttribute('title', info.event.extendedProps.comment || '');
      }
    });
    calendar.render();
  });