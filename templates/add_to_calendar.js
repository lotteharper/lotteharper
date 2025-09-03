function generateCalendarLink(eventDetails) {
  const { title, description, location, start, end } = eventDetails;

  const googleCalendarLink = `https://calendar.google.com/calendar/r/eventedit?text=${encodeURIComponent(title)}&details=${encodeURIComponent(description)}&location=${encodeURIComponent(location)}&dates=${formatDate(start)}/${formatDate(end)}`;

  const yahooCalendarLink = `https://calendar.yahoo.com/?v=60&view=d&type=20&title=${encodeURIComponent(title)}&desc=${encodeURIComponent(description)}&st=${formatDateYahoo(start)}&et=${formatDateYahoo(end)}&in_loc=${encodeURIComponent(location)}`;

  function formatDate(date) {
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    const hours = String(date.getHours()).padStart(2, '0');
    const minutes = String(date.getMinutes()).padStart(2, '0');
    const seconds = String(date.getSeconds()).padStart(2, '0');
    return `${year}${month}${day}T${hours}${minutes}${seconds}Z`;
  }

   function formatDateYahoo(date) {
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    const hours = String(date.getHours()).padStart(2, '0');
    const minutes = String(date.getMinutes()).padStart(2, '0');
    return `${year}${month}${day}T${hours}${minutes}00`;
  }

  return {
    googleCalendar: googleCalendarLink,
    yahooCalendar: yahooCalendarLink
  };
}

const eventDetails = {
  title: '{{ calendar_event_name }}',
  description: '{{ calendar_event_description }}',
  location: '{{ calendar_location }}',
  start: new Date('{{ calendar_time }}'),
  end: new Date('{{ calendar_time|isoformat }}')
};

const calendarLinks = generateCalendarLink(eventDetails);

console.log('Google Calendar Link:', calendarLinks.googleCalendar);
console.log('Yahoo Calendar Link:', calendarLinks.yahooCalendar);
