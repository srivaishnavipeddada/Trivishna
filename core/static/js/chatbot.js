// List of packages for bot logic
const packages = [
    { name: "Kashmir Winter Tour", price: 19999, url: "/packages/1/", duration: 7 },
    { name: "Goa Beach Escape", price: 14999, url: "/packages/2/", duration: 5 },
    { name: "Leh-Ladakh Adventure", price: 24999, url: "/packages/3/", duration: 10 },
    { name: "Kerala Backwaters Tour", price: 17999, url: "/packages/4/", duration: 6 },
    { name: "Mystic Manali Retreat", price: 8500, url: "/packages/5/", duration: 4 },
    { name: "Jaipur Heritage Tour", price: 7200, url: "/packages/6/", duration: 3 },
    { name: "Darjeeling Himalayan Escape", price: 9800, url: "/packages/8/", duration: 5 },
    { name: "Ooty Nature Trail", price: 6700, url: "/packages/9/", duration: 4 },
    { name: "Shimla Snow Getaway", price: 8200, url: "/packages/10/", duration: 5 },
    { name: "Agra Historical Journey", price: 5600, url: "/packages/12/", duration: 2 },
    { name: "Rishikesh River Escape", price: 6100, url: "/packages/13/", duration: 3 },
    { name: "Udaipur Royal Romance", price: 7200, url: "/packages/14/", duration: 4 },
    { name: "Andaman Island Explorer", price: 14500, url: "/packages/15/", duration: 7 },
    { name: "Kodaikanal Hill Escape", price: 6900, url: "/packages/16/", duration: 3 },
    { name: "Pondicherry French Vibes", price: 5900, url: "/packages/17/", duration: 4 },
    { name: "Coorg Coffee Trails", price: 7400, url: "/packages/18/", duration: 5 },
    { name: "Shillong & Cherrapunji", price: 9700, url: "/packages/19/", duration: 6 },
    { name: "Munnar Tea Gardens", price: 6300, url: "/packages/20/", duration: 3 },
    { name: "Tawang Monastery Peace", price: 12000, url: "/packages/21/", duration: 8 },
    { name: "Hampi Ruins Tour", price: 5400, url: "/packages/22/", duration: 2 },
    { name: "Ranthambore Jungle Safari", price: 8700, url: "/packages/23/", duration: 4 },
    { name: "Lonavala Monsoon Magic", price: 4300, url: "/packages/24/", duration: 3 },
  ];
  
  // Function to send bot message
  function sendBotMessage(message) {
    const chatBox = document.getElementById("chat-box");
    const msg = document.createElement("div");
    msg.className = "bot-message";
    msg.innerHTML = message;
    chatBox.appendChild(msg);
    chatBox.scrollTop = chatBox.scrollHeight;
  }
  
  // Function to handle user input
  function handleUserInput(input) {
    const userInput = input.trim().toLowerCase();
    addUserMessage(input);
  
    const chatBox = document.getElementById("chat-box");
    const typingIndicator = document.createElement("div");
    typingIndicator.className = "typing";
    typingIndicator.innerHTML = "Bot is typing...";
    chatBox.appendChild(typingIndicator);
    chatBox.scrollTop = chatBox.scrollHeight;
  
    setTimeout(() => {
      typingIndicator.remove();
  
      if (userInput === "hi" || userInput === "hello") {
        const optionsHTML = `
          <div class="chat-options">
            <button class="chat-option-btn" onclick="window.location.href='/packages/'">📦 Packages</button>
            <button class="chat-option-btn" onclick="alert('Coming soon!')">⭐ Reviews</button>
          </div>
        `;
        sendBotMessage("Hey there! 👋 What would you like to explore?<br>" + optionsHTML);
  
      } else if (userInput.includes("under")) {
        const budget = parseInt(userInput.split("under")[1].replace(/[^\d]/g, ""));
        const matching = packages.filter(p => p.price <= budget);
  
        if (matching.length) {
          let message = `Here are some packages under ₹${budget}:`;
          matching.forEach(pkg => {
            message += `<br><a href="${pkg.url}" class="text-blue-600">${pkg.name} - ₹${pkg.price}</a>`;
          });
          sendBotMessage(message);
        } else {
          sendBotMessage("Sorry! No packages found under your budget.");
        }
  
      } else if (userInput.includes("days")) {
        const daysMatch = userInput.match(/(\d+)\s*days?/);
        if (daysMatch) {
          const days = parseInt(daysMatch[1]);
          const matching = packages.filter(p => p.duration >= days);
  
          if (matching.length) {
            let message = `Here are some packages for ${days}+ day(s):`;
            matching.forEach(pkg => {
              message += `<br><a href="${pkg.url}" class="text-blue-600">${pkg.name} - ${pkg.duration} days, ₹${pkg.price}</a>`;
            });
            sendBotMessage(message);
          } else {
            sendBotMessage("No packages match that duration.");
          }
        } else {
          sendBotMessage("Could you please mention the number of days?");
        }
  
      } else {
        sendBotMessage("Sorry, I didn't get that. Try:<br>👉 <b>'Show me packages under 10000'</b><br>👉 <b>'Suggest me a 5-day trip'</b>");
      }
    }, 1000);
  }
  
  // Function to add user message
  function addUserMessage(message) {
    const chatBox = document.getElementById("chat-box");
    const msg = document.createElement("div");
    msg.className = "user-message";
    msg.innerHTML = message;
    chatBox.appendChild(msg);
    chatBox.scrollTop = chatBox.scrollHeight;
  }
  