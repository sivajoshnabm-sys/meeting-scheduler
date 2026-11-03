const express = require("express");

const {
    schedule,
    scheduleLatest
} = require("../controllers/schedulerController");

const router = express.Router();

router.post("/schedule", schedule);

router.post("/schedule-latest-email", scheduleLatest);

module.exports = router;