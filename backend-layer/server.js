require("dotenv").config();

const express = require("express");
const cors = require("cors");

const schedulerRoutes = require("./routes/schedulerRoutes");
const errorHandler = require("./middleware/errorHandler");
const { startEmailMonitor } = require("./services/emailMonitor");
const app = express();

const PORT = process.env.PORT || 5000;


// Middleware

app.use(cors());

app.use(express.json());


// Health check

app.get("/", (req, res) => {

    res.json({
        status: "success",
        message: "AI Meeting Scheduler Backend is running."
    });
});


// Scheduler routes

app.use("/api/scheduler", schedulerRoutes);


// Error handler

app.use(errorHandler);


// Start server

app.listen(PORT, () => {

    console.log("----------------------------------------------");
    console.log("AI Meeting Scheduler Backend");
    console.log("----------------------------------------------");
    console.log(`Backend running on port ${PORT}`);
    console.log(`AI Layer URL: ${process.env.AI_LAYER_URL}`);
    console.log("----------------------------------------------");
    startEmailMonitor();

});
