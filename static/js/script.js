class AppointmentService {

    static book(data) {
        // Simulated PUT/POST (can connect to backend later)
        console.log("Appointment Data:", data);
        alert("Appointment booked successfully!");
    }
}

function scrollToAppointment() {
    document.getElementById("appointment").scrollIntoView({ behavior: "smooth" });
}

function bookAppointment() {
    const name = document.getElementById("name").value;
    const phone = document.getElementById("phone").value;
    const date = document.getElementById("date").value;

    if (!name || !phone || !date) {
        alert("Please fill all fields");
        return;
    }

    AppointmentService.book({ name, phone, date });
}
