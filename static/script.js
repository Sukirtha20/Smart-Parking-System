function bookSlot(slotId, element) {

    if (element.classList.contains("booked")) {
        alert("Parking slot already occupied.");
        return;
    }

    let vehicle = document.getElementById("vehicle").value;
    let phone = document.getElementById("phone").value;
    let hours = document.getElementById("hours").value;

    if (!vehicle || !phone || !hours) {
        alert("Please enter all parking details.");
        return;
    }

    fetch("/book", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({
            slot: slotId,
            vehicle: vehicle,
            phone: phone,
            hours: hours
        })
    })

    .then(res => res.json())

    .then(data => {

        if (data.success) {

            element.classList.remove("free");
            element.classList.add("booked");

            alert(
`Booking Confirmed

Parking Slot : ${slotId}
Token ID      : ${data.token}
Duration      : ${hours} Hour(s)`
            );

            let message =
`Smart Parking Booking Confirmed

Parking Slot: ${slotId}
Token ID: ${data.token}
Duration: ${hours} Hour(s)

Thank you for choosing Smart Parking System.`;

            let whatsappURL =
`https://wa.me/91${phone}?text=${encodeURIComponent(message)}`;

            window.open(whatsappURL, "_blank");

        } else {

            alert("Unable to complete booking.");

        }

    })

    .catch(error => {

        alert("Server connection error.");

    });
}