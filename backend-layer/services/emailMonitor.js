const axios = require("axios");

const AI_LAYER_URL =
    process.env.AI_LAYER_URL || "http://127.0.0.1:3000";

const POLLING_INTERVAL =
    Number(process.env.EMAIL_POLL_INTERVAL || 30000);


let monitorRunning = false;


async function checkForNewEmails() {

    if (monitorRunning) {
        console.log("Previous email check is still running. Skipping.");
        return;
    }

    monitorRunning = true;

    try {

        console.log("----------------------------------------------");
        console.log("Checking Gmail for new emails...");

        const response = await axios.post(
            `${AI_LAYER_URL}/agent/schedule-latest-email`,
            {},
            {
                timeout: 120000
            }
        );

        const result = response.data;

        console.log("Email monitor result:");
        console.log(result);

        if (result.status === "scheduled") {

            console.log("Meeting scheduled automatically.");
            console.log("Event ID:", result.event_id);
            console.log("Event Link:", result.event_link);

        } else if (result.status === "no_meeting_required") {

            console.log("Email does not require a meeting.");

        } else if (result.status === "no_new_email") {

            console.log("No new email found.");

        } else if (result.status === "no_email") {

            console.log("No email found.");

        } else if (result.status === "no_slot_available") {

            console.log("No suitable meeting slot available.");

        } else if (result.status === "failed") {

            console.log("Email processing failed.");
            console.log("Reason:", result.error);

        }

    } catch (error) {

        console.error(
            "Automatic email check failed:",
            error.message
        );

    } finally {

        monitorRunning = false;
    }
}


function startEmailMonitor() {

    console.log("----------------------------------------------");
    console.log("Automatic Gmail Monitor Started");
    console.log(`Checking every ${POLLING_INTERVAL / 1000} seconds`);
    console.log("----------------------------------------------");

    // Check once immediately
    checkForNewEmails();

    // Continue checking periodically
    setInterval(
        checkForNewEmails,
        POLLING_INTERVAL
    );
}


module.exports = {
    startEmailMonitor
};