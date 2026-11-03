const axios = require("axios");

const AI_LAYER_URL =
    process.env.AI_LAYER_URL || "http://127.0.0.1:3000";

async function scheduleMeeting(emailContent) {
    try {
        const response = await axios.post(
            `${AI_LAYER_URL}/agent/schedule`,
            {
                email_content: emailContent
            },
            {
                timeout: 120000
            }
        );

        return response.data;

    } catch (error) {

        if (error.response) {
            throw new Error(
                error.response.data?.error ||
                error.response.data?.message ||
                "AI layer returned an error."
            );
        }

        if (error.code === "ECONNREFUSED") {
            throw new Error(
                "AI layer is not running. Please start the AI layer on port 3000."
            );
        }

        throw new Error(
            error.message || "Unable to communicate with AI layer."
        );
    }
}


async function scheduleLatestEmail() {
    try {
        const response = await axios.post(
            `${AI_LAYER_URL}/agent/schedule-latest-email`,
            {},
            {
                timeout: 120000
            }
        );

        return response.data;

    } catch (error) {

        if (error.response) {
            throw new Error(
                error.response.data?.error ||
                error.response.data?.message ||
                "AI layer returned an error."
            );
        }

        if (error.code === "ECONNREFUSED") {
            throw new Error(
                "AI layer is not running. Please start the AI layer on port 3000."
            );
        }

        throw new Error(
            error.message || "Unable to communicate with AI layer."
        );
    }
}


module.exports = {
    scheduleMeeting,
    scheduleLatestEmail
};