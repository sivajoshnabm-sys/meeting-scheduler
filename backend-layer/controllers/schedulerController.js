const {
    scheduleMeeting,
    scheduleLatestEmail
} = require("../services/aiService");


async function schedule(req, res, next) {

    try {

        const { email_content } = req.body;

        if (!email_content || !email_content.trim()) {
            return res.status(400).json({
                status: "failed",
                message: "Email content is required."
            });
        }

        const result = await scheduleMeeting(email_content);

        return res.status(200).json(result);

    } catch (error) {

        next(error);
    }
}


async function scheduleLatest(req, res, next) {

    try {

        const result = await scheduleLatestEmail();

        return res.status(200).json(result);

    } catch (error) {

        next(error);
    }
}


module.exports = {
    schedule,
    scheduleLatest
};