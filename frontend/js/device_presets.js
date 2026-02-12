/**
 * Device presets builder
 * - Select a device (gigbar / keobin)
 * - Use scene-builder-style UI to edit channels
 * - Save/load/apply presets via /api/device-presets and /api/apply/device-preset
 */

(function () {
  "use strict";

  // DMX mode definitions (copied from original scene-builder)
  const MODE_VALUES = {
    gigbar: {
      par_1: {
        off: {1: 0, 2: 0, 3: 0, 4: 0, 5: 0},
        red: {1: 255, 2: 0, 3: 0, 4: 0, 5: 79},
        green: {1: 0, 2: 255, 3: 0, 4: 0, 5: 79},
        blue: {1: 0, 2: 0, 3: 255, 4: 0, 5: 79},
        uv: {1: 0, 2: 0, 3: 0, 4: 255, 5: 79},
        red_strobe: {1: 255, 2: 0, 3: 0, 4: 0, 5: 249},
        green_strobe: {1: 0, 2: 255, 3: 0, 4: 0, 5: 249},
        blue_strobe: {1: 0, 2: 0, 3: 255, 4: 0, 5: 249},
        uv_strobe: {1: 0, 2: 0, 3: 0, 4: 255, 5: 249}
      },
      par_2: {
        off: {6: 0, 7: 0, 8: 0, 9: 0, 10: 0},
        red: {6: 255, 7: 0, 8: 0, 9: 0, 10: 79},
        green: {6: 0, 7: 255, 8: 0, 9: 0, 10: 79},
        blue: {6: 0, 7: 0, 8: 255, 9: 0, 10: 79},
        uv: {6: 0, 7: 0, 8: 0, 9: 255, 10: 79},
        red_strobe: {6: 255, 7: 0, 8: 0, 9: 0, 10: 249},
        green_strobe: {6: 0, 7: 255, 8: 0, 9: 0, 10: 249},
        blue_strobe: {6: 0, 7: 0, 8: 255, 9: 0, 10: 249},
        uv_strobe: {6: 0, 7: 0, 8: 0, 9: 255, 10: 249}
      },
      derby_1: {
        off: {11: 0, 12: 0, 13: 0},
        red_cw: {11: 49, 12: 0, 13: 127},
        green_cw: {11: 74, 12: 0, 13: 127},
        blue_cw: {11: 99, 12: 0, 13: 127},
        rg_cw: {11: 124, 12: 0, 13: 127},
        rb_cw: {11: 149, 12: 0, 13: 127},
        gb_cw: {11: 174, 12: 0, 13: 127},
        rgb_cw: {11: 199, 12: 0, 13: 127},
        red_cc: {11: 49, 12: 0, 13: 255},
        green_cc: {11: 74, 12: 0, 13: 255},
        blue_cc: {11: 99, 12: 0, 13: 255},
        rg_cc: {11: 124, 12: 0, 13: 255},
        rb_cc: {11: 149, 12: 0, 13: 255},
        gb_cc: {11: 174, 12: 0, 13: 255},
        rgb_cc: {11: 199, 12: 0, 13: 255},
        strobe_red_cw: {11: 49, 12: 250, 13: 127},
        strobe_green_cw: {11: 74, 12: 250, 13: 127},
        strobe_blue_cw: {11: 99, 12: 250, 13: 127},
        strobe_rg_cw: {11: 124, 12: 250, 13: 127},
        strobe_rb_cw: {11: 149, 12: 250, 13: 127},
        strobe_gb_cw: {11: 174, 12: 250, 13: 127},
        strobe_rgb_cw: {11: 199, 12: 250, 13: 127},
        strobe_red_cc: {11: 49, 12: 250, 13: 255},
        strobe_green_cc: {11: 74, 12: 250, 13: 255},
        strobe_blue_cc: {11: 99, 12: 250, 13: 255},
        strobe_rg_cc: {11: 124, 12: 250, 13: 255},
        strobe_rb_cc: {11: 149, 12: 250, 13: 255},
        strobe_gb_cc: {11: 174, 12: 250, 13: 255},
        strobe_rgb_cc: {11: 199, 12: 250, 13: 255}
      },
      derby_2: {
        off: {14: 0, 15: 0, 16: 0},
        red_cw: {14: 49, 15: 0, 16: 127},
        green_cw: {14: 74, 15: 0, 16: 127},
        blue_cw: {14: 99, 15: 0, 16: 127},
        rg_cw: {14: 124, 15: 0, 16: 127},
        rb_cw: {14: 149, 15: 0, 16: 127},
        gb_cw: {14: 174, 15: 0, 16: 127},
        rgb_cw: {14: 199, 15: 0, 16: 127},
        red_cc: {14: 49, 15: 0, 16: 255},
        green_cc: {14: 74, 15: 0, 16: 255},
        blue_cc: {14: 99, 15: 0, 16: 255},
        rg_cc: {14: 124, 15: 0, 16: 255},
        rb_cc: {14: 149, 15: 0, 16: 255},
        gb_cc: {14: 174, 15: 0, 16: 255},
        rgb_cc: {14: 199, 15: 0, 16: 255},
        strobe_red_cw: {14: 49, 15: 250, 16: 127},
        strobe_green_cw: {14: 74, 15: 250, 16: 127},
        strobe_blue_cw: {14: 99, 15: 250, 16: 127},
        strobe_rg_cw: {14: 124, 15: 250, 16: 127},
        strobe_rb_cw: {14: 149, 15: 250, 16: 127},
        strobe_gb_cw: {14: 174, 15: 250, 16: 127},
        strobe_rgb_cw: {14: 199, 15: 250, 16: 127},
        strobe_red_cc: {14: 49, 15: 250, 16: 255},
        strobe_green_cc: {14: 74, 15: 250, 16: 255},
        strobe_blue_cc: {14: 99, 15: 250, 16: 255},
        strobe_rg_cc: {14: 124, 15: 250, 16: 255},
        strobe_rb_cc: {14: 149, 15: 250, 16: 255},
        strobe_gb_cc: {14: 174, 15: 250, 16: 255},
        strobe_rgb_cc: {14: 199, 15: 250, 16: 255}
      },
      laser: {
        off: {17: 0, 18: 0, 19: 0},
        red_cw: {17: 79, 18: 0, 19: 127},
        red_cc: {17: 79, 18: 0, 19: 255},
        green_cw: {17: 119, 18: 0, 19: 127},
        green_cc: {17: 119, 18: 0, 19: 255},
        rg_cw: {17: 159, 18: 0, 19: 127},
        rg_cc: {17: 159, 18: 0, 19: 255},
        r_gstrobe_cw: {17: 199, 18: 0, 19: 127},
        r_gstrobe_cc: {17: 199, 18: 0, 19: 255},
        rstrobe_g_cw: {17: 239, 18: 0, 19: 127},
        rstrobe_g_cc: {17: 239, 18: 0, 19: 255},
        auto_cw: {17: 255, 18: 0, 19: 127},
        auto_cc: {17: 255, 18: 0, 19: 255}
      },
      strobe: {
        off: {20: 0, 21: 0, 22: 0, 23: 0},
        slowW: {20: 190, 21: 75, 22: 0, 23: 0},
        slowUV: {20: 190, 21: 0, 22: 100, 23: 0},
        fastW: {20: 209, 21: 75, 22: 0, 23: 0},
        fastUV: {20: 209, 21: 0, 22: 100, 23: 0},
        soundW: {20: 255, 21: 75, 22: 0, 23: 0},
        soundUV: {20: 255, 21: 0, 22: 100, 23: 0}
      }
    },
    keobin: {
      green_laser: {
        off: {2: 0},
        on: {2: 255, 6: 255}
      },
      red_laser_1: {
        off: {3: 0},
        on: {3: 255, 6: 255}
      },
      blue_laser: {
        off: {4: 0},
        on: {4: 255, 6: 255}
      },
      red_laser_2: {
        off: {5: 0},
        on: {5: 255, 6: 255}
      },
      magic_ball: {
        red_1: {7: 255},
        green_1: {8: 255},
        blue_1: {9: 255},
        white_1: {10: 255},
        red_2: {11: 255},
        green_2: {12: 255},
        blue_2: {13: 255}
      },
      strobe: {
        off: {14: 0, 15: 0, 16: 0, 17: 0, 18: 0},
        red_strobe_slow: {14: 30, 15: 255, 16: 0, 17: 0, 18: 0},
        green_strobe_slow: {14: 30, 15: 0, 16: 255, 17: 0, 18: 0},
        blue_strobe_slow: {14: 30, 15: 0, 16: 0, 17: 255, 18: 0},
        white_strobe_slow: {14: 30, 15: 255, 16: 255, 17: 255, 18: 0},
        red_UV_strobe_slow: {14: 30, 15: 255, 16: 0, 17: 0, 18: 255},
        green_UV_strobe_slow: {14: 30, 15: 0, 16: 255, 17: 0, 18: 255},
        blue_UV_strobe_slow: {14: 30, 15: 0, 16: 0, 17: 255, 18: 255},
        white_UV_strobe_slow: {14: 30, 15: 255, 16: 255, 17: 255, 18: 255},
        red_strobe_fast: {14: 255, 15: 255, 16: 0, 17: 0, 18: 0},
        green_strobe_fast: {14: 255, 15: 0, 16: 255, 17: 0, 18: 0},
        blue_strobe_fast: {14: 255, 15: 0, 16: 0, 17: 255, 18: 0},
        white_strobe_fast: {14: 255, 15: 255, 16: 255, 17: 255, 18: 0},
        red_UV_strobe_fast: {14: 255, 15: 255, 16: 0, 17: 0, 18: 255},
        green_UV_strobe_fast: {14: 255, 15: 0, 16: 255, 17: 0, 18: 255},
        blue_UV_strobe_fast: {14: 255, 15: 0, 16: 0, 17: 255, 18: 255},
        white_UV_strobe_fast: {14: 255, 15: 255, 16: 255, 17: 255, 18: 255}
      }
    }
  };

  function initialState() {
    return {
      gigbar: {
        par_1: "off",
        par_2: "off",
        derby_1: "off",
        derby_2: "off",
        laser: "off",
        strobe: "off"
      },
      keobin: {
        green_laser: "off",
        red_laser_1: "off",
        blue_laser: "off",
        red_laser_2: "off",
        magic_ball: [],
        strobe: "off"
      }
    };
  }

  let currentState = initialState();
  let currentDeviceId = "";
  let allPresets = [];

  function generateDMXValues() {
    const gigbar = {};
    const keobin = {};
    for (let i = 1; i <= 23; i++) gigbar[String(i)] = 0;
    for (let i = 1; i <= 18; i++) keobin[String(i)] = 0;

    for (const [subdevice, mode] of Object.entries(currentState.gigbar)) {
      const values = MODE_VALUES.gigbar[subdevice][mode];
      if (values) {
        for (const [ch, val] of Object.entries(values)) {
          gigbar[ch] = val;
        }
      }
    }

    for (const [subdevice, mode] of Object.entries(currentState.keobin)) {
      if (subdevice === "magic_ball") continue;
      const values = MODE_VALUES.keobin[subdevice][mode];
      if (values) {
        for (const [ch, val] of Object.entries(values)) {
          keobin[ch] = Math.max(keobin[ch], val);
        }
      }
    }

    for (const mode of currentState.keobin.magic_ball) {
      const values = MODE_VALUES.keobin.magic_ball[mode];
      if (values) {
        for (const [ch, val] of Object.entries(values)) {
          keobin[ch] = val;
        }
      }
    }

    return { gigbar, keobin };
  }

  function deviceChannelArray(deviceId) {
    const dmx = generateDMXValues();
    if (deviceId === "gigbar") {
      const obj = dmx.gigbar;
      const out = [];
      for (let i = 1; i <= 23; i++) out.push(obj[String(i)] || 0);
      return out;
    }
    if (deviceId === "keobin") {
      const obj = dmx.keobin;
      const out = [];
      for (let i = 1; i <= 18; i++) out.push(obj[String(i)] || 0);
      return out;
    }
    return [];
  }

  function renderPreview() {
    const preview = document.getElementById("device-preview");
    if (!preview || !currentDeviceId) return;
    const dmx = generateDMXValues();
    let html = "";
    const obj = currentDeviceId === "gigbar" ? dmx.gigbar : dmx.keobin;
    const maxCh = currentDeviceId === "gigbar" ? 23 : 18;
    for (let i = 1; i <= maxCh; i++) {
      const val = obj[String(i)] || 0;
      html +=
        '<div class="dmx-channel ' +
        (val > 0 ? "active" : "") +
        '"><div class="ch-num">' +
        i +
        '</div><div class="ch-val">' +
        val +
        "</div></div>";
    }
    preview.innerHTML = html;
  }

  function setupModeButtons() {
    document.querySelectorAll(".mode-group").forEach(function (group) {
      const device = group.dataset.device;
      const subdevice = group.dataset.subdevice;
      const exclusive = group.dataset.exclusive === "true";

      group.querySelectorAll(".mode-btn").forEach(function (btn) {
        btn.addEventListener("click", function () {
          const mode = btn.dataset.mode;

          if (exclusive) {
            group.querySelectorAll(".mode-btn").forEach(function (b) {
              b.classList.remove("selected");
            });
            btn.classList.add("selected");
            currentState[device][subdevice] = mode;
          } else {
            if (btn.classList.contains("selected-multi")) {
              btn.classList.remove("selected-multi");
              currentState[device][subdevice] = currentState[device][subdevice].filter(function (m) {
                return m !== mode;
              });
            } else {
              btn.classList.add("selected-multi");
              currentState[device][subdevice].push(mode);
            }
          }

          renderPreview();
        });
      });
    });
  }

  function reverseMapFromChannels(deviceId, channels) {
    currentState = initialState();
    if (deviceId === "gigbar") {
      const values = { gigbar: {}, keobin: {} };
      for (let i = 1; i <= 23; i++) {
        values.gigbar[String(i)] = channels[i - 1] || 0;
      }
      // Gigbar reverse mapping (from scene-builder)
      for (const [subdevice, modes] of Object.entries(MODE_VALUES.gigbar)) {
        for (const [mode, chVals] of Object.entries(modes)) {
          if (mode === "off") continue;
          let matches = true;
          for (const [ch, val] of Object.entries(chVals)) {
            if (values.gigbar[ch] !== val) {
              matches = false;
              break;
            }
          }
          if (matches) {
            currentState.gigbar[subdevice] = mode;
            break;
          }
        }
      }
    } else if (deviceId === "keobin") {
      const values = { gigbar: {}, keobin: {} };
      for (let i = 1; i <= 18; i++) {
        values.keobin[String(i)] = channels[i - 1] || 0;
      }
      // Keobin lasers reverse mapping
      for (const subdevice of ["green_laser", "red_laser_1", "blue_laser", "red_laser_2"]) {
        const onMode = MODE_VALUES.keobin[subdevice].on;
        let matches = true;
        for (const [ch, val] of Object.entries(onMode)) {
          if (ch === "6") continue;
          if (values.keobin[ch] !== val) {
            matches = false;
            break;
          }
        }
        if (matches) {
          currentState.keobin[subdevice] = "on";
        }
      }
      // Keobin strobe reverse mapping
      for (const [mode, chVals] of Object.entries(MODE_VALUES.keobin.strobe)) {
        if (mode === "off") continue;
        let matches = true;
        for (const [ch, val] of Object.entries(chVals)) {
          if (values.keobin[ch] !== val) {
            matches = false;
            break;
          }
        }
        if (matches) {
          currentState.keobin.strobe = mode;
          break;
        }
      }
      // Magic ball reverse mapping
      for (const [mode, chVals] of Object.entries(MODE_VALUES.keobin.magic_ball)) {
        for (const [ch, val] of Object.entries(chVals)) {
          if (values.keobin[ch] === val) {
            if (!currentState.keobin.magic_ball.includes(mode)) {
              currentState.keobin.magic_ball.push(mode);
            }
          }
        }
      }
    }
  }

  function updateButtonsFromState() {
    document.querySelectorAll(".mode-group").forEach(function (group) {
      const device = group.dataset.device;
      const subdevice = group.dataset.subdevice;
      const exclusive = group.dataset.exclusive === "true";

      if (exclusive) {
        const mode = currentState[device][subdevice];
        group.querySelectorAll(".mode-btn").forEach(function (btn) {
          btn.classList.toggle("selected", btn.dataset.mode === mode);
        });
      } else {
        const modes = currentState[device][subdevice];
        group.querySelectorAll(".mode-btn").forEach(function (btn) {
          btn.classList.toggle("selected-multi", modes.includes(btn.dataset.mode));
        });
      }
    });
  }

  function deviceCardHtml(deviceId) {
    if (deviceId === "gigbar") {
      return (
        '<div class="card">' +
        "<h2>GIGBAR</h2>" +
        '<div class="subdevice">' +
        "<h3>PAR 1</h3>" +
        '<div class="mode-group" data-device="gigbar" data-subdevice="par_1" data-exclusive="true">' +
        '<button class="mode-btn selected" data-mode="off">OFF</button>' +
        '<button class="mode-btn" data-mode="red">RED</button>' +
        '<button class="mode-btn" data-mode="green">GREEN</button>' +
        '<button class="mode-btn" data-mode="blue">BLUE</button>' +
        '<button class="mode-btn" data-mode="uv">UV</button>' +
        '<div class="strobe-header">STROBE:</div>' +
        '<button class="mode-btn" data-mode="red_strobe">R STROBE</button>' +
        '<button class="mode-btn" data-mode="green_strobe">G STROBE</button>' +
        '<button class="mode-btn" data-mode="blue_strobe">B STROBE</button>' +
        '<button class="mode-btn" data-mode="uv_strobe">UV STROBE</button>' +
        "</div></div>" +
        '<div class="subdevice">' +
        "<h3>PAR 2</h3>" +
        '<div class="mode-group" data-device="gigbar" data-subdevice="par_2" data-exclusive="true">' +
        '<button class="mode-btn selected" data-mode="off">OFF</button>' +
        '<button class="mode-btn" data-mode="red">RED</button>' +
        '<button class="mode-btn" data-mode="green">GREEN</button>' +
        '<button class="mode-btn" data-mode="blue">BLUE</button>' +
        '<button class="mode-btn" data-mode="uv">UV</button>' +
        '<div class="strobe-header">STROBE:</div>' +
        '<button class="mode-btn" data-mode="red_strobe">R STROBE</button>' +
        '<button class="mode-btn" data-mode="green_strobe">G STROBE</button>' +
        '<button class="mode-btn" data-mode="blue_strobe">B STROBE</button>' +
        '<button class="mode-btn" data-mode="uv_strobe">UV STROBE</button>' +
        "</div></div>" +
        '<div class="subdevice">' +
        "<h3>DERBY 1</h3>" +
        '<div class="mode-group" data-device="gigbar" data-subdevice="derby_1" data-exclusive="true">' +
        '<button class="mode-btn selected" data-mode="off">OFF</button>' +
        '<button class="mode-btn" data-mode="red_cw">R CW</button>' +
        '<button class="mode-btn" data-mode="green_cw">G CW</button>' +
        '<button class="mode-btn" data-mode="blue_cw">B CW</button>' +
        '<button class="mode-btn" data-mode="rg_cw">RG CW</button>' +
        '<button class="mode-btn" data-mode="rb_cw">RB CW</button>' +
        '<button class="mode-btn" data-mode="gb_cw">GB CW</button>' +
        '<button class="mode-btn" data-mode="rgb_cw">RGB CW</button>' +
        '<button class="mode-btn" data-mode="red_cc">R CC</button>' +
        '<button class="mode-btn" data-mode="green_cc">G CC</button>' +
        '<button class="mode-btn" data-mode="blue_cc">B CC</button>' +
        '<button class="mode-btn" data-mode="rg_cc">RG CC</button>' +
        '<button class="mode-btn" data-mode="rb_cc">RB CC</button>' +
        '<button class="mode-btn" data-mode="gb_cc">GB CC</button>' +
        '<button class="mode-btn" data-mode="rgb_cc">RGB CC</button>' +
        '<div class="strobe-header">STROBE:</div>' +
        '<button class="mode-btn" data-mode="strobe_red_cw">R CW</button>' +
        '<button class="mode-btn" data-mode="strobe_green_cw">G CW</button>' +
        '<button class="mode-btn" data-mode="strobe_blue_cw">B CW</button>' +
        '<button class="mode-btn" data-mode="strobe_rg_cw">RG CW</button>' +
        '<button class="mode-btn" data-mode="strobe_rb_cw">RB CW</button>' +
        '<button class="mode-btn" data-mode="strobe_gb_cw">GB CW</button>' +
        '<button class="mode-btn" data-mode="strobe_rgb_cw">RGB CW</button>' +
        '<button class="mode-btn" data-mode="strobe_red_cc">R CC</button>' +
        '<button class="mode-btn" data-mode="strobe_green_cc">G CC</button>' +
        '<button class="mode-btn" data-mode="strobe_blue_cc">B CC</button>' +
        '<button class="mode-btn" data-mode="strobe_rg_cc">RG CC</button>' +
        '<button class="mode-btn" data-mode="strobe_rb_cc">RB CC</button>' +
        '<button class="mode-btn" data-mode="strobe_gb_cc">GB CC</button>' +
        '<button class="mode-btn" data-mode="strobe_rgb_cc">RGB CC</button>' +
        "</div></div>" +
        '<div class="subdevice">' +
        "<h3>DERBY 2</h3>" +
        '<div class="mode-group" data-device="gigbar" data-subdevice="derby_2" data-exclusive="true">' +
        '<button class="mode-btn selected" data-mode="off">OFF</button>' +
        '<button class="mode-btn" data-mode="red_cw">R CW</button>' +
        '<button class="mode-btn" data-mode="green_cw">G CW</button>' +
        '<button class="mode-btn" data-mode="blue_cw">B CW</button>' +
        '<button class="mode-btn" data-mode="rg_cw">RG CW</button>' +
        '<button class="mode-btn" data-mode="rb_cw">RB CW</button>' +
        '<button class="mode-btn" data-mode="gb_cw">GB CW</button>' +
        '<button class="mode-btn" data-mode="rgb_cw">RGB CW</button>' +
        '<button class="mode-btn" data-mode="red_cc">R CC</button>' +
        '<button class="mode-btn" data-mode="green_cc">G CC</button>' +
        '<button class="mode-btn" data-mode="blue_cc">B CC</button>' +
        '<button class="mode-btn" data-mode="rg_cc">RG CC</button>' +
        '<button class="mode-btn" data-mode="rb_cc">RB CC</button>' +
        '<button class="mode-btn" data-mode="gb_cc">GB CC</button>' +
        '<button class="mode-btn" data-mode="rgb_cc">RGB CC</button>' +
        '<div class="strobe-header">STROBE:</div>' +
        '<button class="mode-btn" data-mode="strobe_red_cw">R CW</button>' +
        '<button class="mode-btn" data-mode="strobe_green_cw">G CW</button>' +
        '<button class="mode-btn" data-mode="strobe_blue_cw">B CW</button>' +
        '<button class="mode-btn" data-mode="strobe_rg_cw">RG CW</button>' +
        '<button class="mode-btn" data-mode="strobe_rb_cw">RB CW</button>' +
        '<button class="mode-btn" data-mode="strobe_gb_cw">GB CW</button>' +
        '<button class="mode-btn" data-mode="strobe_rgb_cw">RGB CW</button>' +
        '<button class="mode-btn" data-mode="strobe_red_cc">R CC</button>' +
        '<button class="mode-btn" data-mode="strobe_green_cc">G CC</button>' +
        '<button class="mode-btn" data-mode="strobe_blue_cc">B CC</button>' +
        '<button class="mode-btn" data-mode="strobe_rg_cc">RG CC</button>' +
        '<button class="mode-btn" data-mode="strobe_rb_cc">RB CC</button>' +
        '<button class="mode-btn" data-mode="strobe_gb_cc">GB CC</button>' +
        '<button class="mode-btn" data-mode="strobe_rgb_cc">RGB CC</button>' +
        "</div></div>" +
        '<div class="subdevice">' +
        "<h3>LASER</h3>" +
        '<div class="mode-group" data-device="gigbar" data-subdevice="laser" data-exclusive="true">' +
        '<button class="mode-btn selected" data-mode="off">OFF</button>' +
        '<button class="mode-btn" data-mode="red_cw">R CW</button>' +
        '<button class="mode-btn" data-mode="red_cc">R CC</button>' +
        '<button class="mode-btn" data-mode="green_cw">G CW</button>' +
        '<button class="mode-btn" data-mode="green_cc">G CC</button>' +
        '<button class="mode-btn" data-mode="rg_cw">RG CW</button>' +
        '<button class="mode-btn" data-mode="rg_cc">RG CC</button>' +
        '<button class="mode-btn" data-mode="r_gstrobe_cw">R+Gs CW</button>' +
        '<button class="mode-btn" data-mode="r_gstrobe_cc">R+Gs CC</button>' +
        '<button class="mode-btn" data-mode="rstrobe_g_cw">Rs+G CW</button>' +
        '<button class="mode-btn" data-mode="rstrobe_g_cc">Rs+G CC</button>' +
        '<button class="mode-btn" data-mode="auto_cw">AUTO CW</button>' +
        '<button class="mode-btn" data-mode="auto_cc">AUTO CC</button>' +
        "</div></div>" +
        '<div class="subdevice">' +
        "<h3>STROBE</h3>" +
        '<div class="mode-group" data-device="gigbar" data-subdevice="strobe" data-exclusive="true">' +
        '<button class="mode-btn selected" data-mode="off">OFF</button>' +
        '<button class="mode-btn" data-mode="slowW">SLOW W</button>' +
        '<button class="mode-btn" data-mode="slowUV">SLOW UV</button>' +
        '<button class="mode-btn" data-mode="fastW">FAST W</button>' +
        '<button class="mode-btn" data-mode="fastUV">FAST UV</button>' +
        '<button class="mode-btn" data-mode="soundW">SOUND W</button>' +
        '<button class="mode-btn" data-mode="soundUV">SOUND UV</button>' +
        "</div></div></div>"
      );
    }

    if (deviceId === "keobin") {
      return (
        '<div class="card">' +
        "<h2>KEOBIN</h2>" +
        '<div class="subdevice">' +
        "<h3>GREEN LASER</h3>" +
        '<div class="mode-group" data-device="keobin" data-subdevice="green_laser" data-exclusive="true">' +
        '<button class="mode-btn selected" data-mode="off">OFF</button>' +
        '<button class="mode-btn" data-mode="on">ON</button>' +
        "</div></div>" +
        '<div class="subdevice">' +
        "<h3>RED LASER 1</h3>" +
        '<div class="mode-group" data-device="keobin" data-subdevice="red_laser_1" data-exclusive="true">' +
        '<button class="mode-btn selected" data-mode="off">OFF</button>' +
        '<button class="mode-btn" data-mode="on">ON</button>' +
        "</div></div>" +
        '<div class="subdevice">' +
        "<h3>BLUE LASER</h3>" +
        '<div class="mode-group" data-device="keobin" data-subdevice="blue_laser" data-exclusive="true">' +
        '<button class="mode-btn selected" data-mode="off">OFF</button>' +
        '<button class="mode-btn" data-mode="on">ON</button>' +
        "</div></div>" +
        '<div class="subdevice">' +
        "<h3>RED LASER 2</h3>" +
        '<div class="mode-group" data-device="keobin" data-subdevice="red_laser_2" data-exclusive="true">' +
        '<button class="mode-btn selected" data-mode="off">OFF</button>' +
        '<button class="mode-btn" data-mode="on">ON</button>' +
        "</div></div>" +
        '<div class="subdevice">' +
        "<h3>MAGIC BALL (Multi-select)</h3>" +
        '<div class="mode-group" data-device="keobin" data-subdevice="magic_ball" data-exclusive="false">' +
        '<button class="mode-btn" data-mode="red_1">RED 1</button>' +
        '<button class="mode-btn" data-mode="green_1">GREEN 1</button>' +
        '<button class="mode-btn" data-mode="blue_1">BLUE 1</button>' +
        '<button class="mode-btn" data-mode="white_1">WHITE 1</button>' +
        '<button class="mode-btn" data-mode="red_2">RED 2</button>' +
        '<button class="mode-btn" data-mode="green_2">GREEN 2</button>' +
        '<button class="mode-btn" data-mode="blue_2">BLUE 2</button>' +
        "</div></div>" +
        '<div class="subdevice">' +
        "<h3>STROBE</h3>" +
        '<div class="mode-group" data-device="keobin" data-subdevice="strobe" data-exclusive="true">' +
        '<button class="mode-btn selected" data-mode="off">OFF</button>' +
        '<div class="strobe-header">SLOW:</div>' +
        '<button class="mode-btn" data-mode="red_strobe_slow">R SLOW</button>' +
        '<button class="mode-btn" data-mode="green_strobe_slow">G SLOW</button>' +
        '<button class="mode-btn" data-mode="blue_strobe_slow">B SLOW</button>' +
        '<button class="mode-btn" data-mode="white_strobe_slow">W SLOW</button>' +
        '<button class="mode-btn" data-mode="red_UV_strobe_slow">R+UV SLOW</button>' +
        '<button class="mode-btn" data-mode="green_UV_strobe_slow">G+UV SLOW</button>' +
        '<button class="mode-btn" data-mode="blue_UV_strobe_slow">B+UV SLOW</button>' +
        '<button class="mode-btn" data-mode="white_UV_strobe_slow">W+UV SLOW</button>' +
        '<div class="strobe-header">FAST:</div>' +
        '<button class="mode-btn" data-mode="red_strobe_fast">R FAST</button>' +
        '<button class="mode-btn" data-mode="green_strobe_fast">G FAST</button>' +
        '<button class="mode-btn" data-mode="blue_strobe_fast">B FAST</button>' +
        '<button class="mode-btn" data-mode="white_strobe_fast">W FAST</button>' +
        '<button class="mode-btn" data-mode="red_UV_strobe_fast">R+UV FAST</button>' +
        '<button class="mode-btn" data-mode="green_UV_strobe_fast">G+UV FAST</button>' +
        '<button class="mode-btn" data-mode="blue_UV_strobe_fast">B+UV FAST</button>' +
        '<button class="mode-btn" data-mode="white_UV_strobe_fast">W+UV FAST</button>' +
        "</div></div></div>"
      );
    }
    return "";
  }

  function renderBuilderForDevice(deviceId) {
    const root = document.getElementById("device-builder-root");
    const status = document.getElementById("device-presets-status");
    if (!root) return;
    if (!deviceId) {
      root.style.display = "none";
      root.innerHTML = "";
      if (status) status.textContent = "Select a device to edit and save presets.";
      return;
    }
    currentDeviceId = deviceId;
    currentState = initialState();

    root.style.display = "block";
    root.innerHTML =
      '<div class="grid grid-2">' +
      '<div class="device-controls">' +
      deviceCardHtml(deviceId) +
      "</div>" +
      "<div>" +
      '<div class="card">' +
      "<h2>Save preset</h2>" +
      '<div class="form-group">' +
      '<label for="preset-name">Preset name</label>' +
      '<input type="text" id="preset-name" placeholder="Enter preset name">' +
      "</div>" +
      '<div class="flex gap-md">' +
      '<button class="btn btn-primary" id="btn-save-preset">Save preset</button>' +
      '<button class="btn btn-secondary" id="btn-reset-preset">Reset</button>' +
      "</div>" +
      "<h3 class=\"mt-md\">DMX Preview</h3>" +
      '<div id="device-preview" class="dmx-preview"></div>' +
      "</div>" +
      '<div class="card">' +
      "<h2>Saved presets</h2>" +
      '<div id="preset-list"></div>' +
      "</div>" +
      "</div>" +
      "</div>";

    setupModeButtons();
    updateButtonsFromState();
    renderPreview();

    const saveBtn = document.getElementById("btn-save-preset");
    const resetBtn = document.getElementById("btn-reset-preset");
    if (saveBtn) {
      saveBtn.onclick = savePreset;
    }
    if (resetBtn) {
      resetBtn.onclick = function () {
        currentState = initialState();
        updateButtonsFromState();
        renderPreview();
      };
    }

    if (status) status.textContent = "";
    loadPresetsForDevice(deviceId);
  }

  function slugify(name) {
    return name.toLowerCase().trim().replace(/\s+/g, "_").replace(/[^a-z0-9_]/g, "");
  }

  function renderPresetList() {
    const list = document.getElementById("preset-list");
    if (!list) return;
    const presets = allPresets.filter(function (p) {
      return p.device === currentDeviceId;
    });
    if (presets.length === 0) {
      list.innerHTML = '<div class="status">No presets saved for this device</div>';
      return;
    }
    list.innerHTML = presets
      .map(function (p) {
        return (
          '<div class="scene-item" data-id="' +
          p.id +
          '">' +
          "<span>" +
          p.id +
          "</span>" +
          "<div>" +
          '<button class="btn btn-small btn-primary" data-action="apply" data-id="' +
          p.id +
          '">APPLY</button>' +
          '<button class="btn btn-small btn-danger" data-action="delete" data-id="' +
          p.id +
          '">DEL</button>' +
          "</div>" +
          "</div>"
        );
      })
      .join("");

    list.querySelectorAll("button[data-action]").forEach(function (btn) {
      const action = btn.getAttribute("data-action");
      const id = btn.getAttribute("data-id");
      if (action === "apply") {
        btn.onclick = function (ev) {
          ev.stopPropagation();
          applyPreset(id);
        };
      } else if (action === "delete") {
        btn.onclick = function (ev) {
          ev.stopPropagation();
          deletePreset(id);
        };
      }
    });

    list.querySelectorAll(".scene-item").forEach(function (row) {
      const id = row.getAttribute("data-id");
      row.onclick = function () {
        loadPresetIntoEditor(id);
      };
    });
  }

  function loadPresetsForDevice(deviceId) {
    API.get("/device-presets")
      .then(function (presets) {
        allPresets = presets || [];
        renderPresetList();
      })
      .catch(function (err) {
        console.error("Failed to load device presets", err);
      });
  }

  function savePreset() {
    if (!currentDeviceId) return;
    const nameInput = document.getElementById("preset-name");
    const status = document.getElementById("device-presets-status");
    const rawName = nameInput ? nameInput.value.trim() : "";
    if (!rawName) {
      if (status) status.textContent = "Enter a preset name first.";
      return;
    }
    const id = slugify(rawName);
    const body = {
      id: id,
      device: currentDeviceId,
      channel_values: deviceChannelArray(currentDeviceId)
    };
    API.post("/device-presets", body)
      .then(function (preset) {
        const idx = allPresets.findIndex(function (p) {
          return p.id === preset.id && p.device === preset.device;
        });
        if (idx >= 0) allPresets[idx] = preset;
        else allPresets.push(preset);
        renderPresetList();
        if (nameInput) nameInput.value = "";
        if (status) status.textContent = "Preset saved.";
      })
      .catch(function (err) {
        if (status) status.textContent = "Failed to save preset: " + err.message;
      });
  }

  function applyPreset(presetId) {
    if (!currentDeviceId) return;
    const status = document.getElementById("device-presets-status");
    API.post("/apply/device-preset/" + encodeURIComponent(currentDeviceId) + "/" + encodeURIComponent(presetId))
      .then(function () {
        if (status) status.textContent = "Preset applied.";
      })
      .catch(function (err) {
        if (status) status.textContent = "Failed to apply preset: " + err.message;
      });
  }

  function deletePreset(presetId) {
    const status = document.getElementById("device-presets-status");
    API.delete("/device-presets/" + encodeURIComponent(presetId))
      .then(function () {
        allPresets = allPresets.filter(function (p) {
          return p.id !== presetId;
        });
        renderPresetList();
        if (status) status.textContent = "Preset deleted.";
      })
      .catch(function (err) {
        if (status) status.textContent = "Failed to delete preset: " + err.message;
      });
  }

  function loadPresetIntoEditor(presetId) {
    const preset = allPresets.find(function (p) {
      return p.id === presetId && p.device === currentDeviceId;
    });
    if (!preset) return;
    reverseMapFromChannels(currentDeviceId, preset.channel_values || []);
    updateButtonsFromState();
    renderPreview();
    const nameInput = document.getElementById("preset-name");
    if (nameInput) nameInput.value = preset.id;
  }

  function populateDevicesDropdown() {
    const select = document.getElementById("device-select");
    const status = document.getElementById("device-presets-status");
    if (!select) return;
    API.get("/devices")
      .then(function (devices) {
        const supportedIds = Object.keys(MODE_VALUES);
        const usable = (devices || []).filter(function (d) {
          return supportedIds.includes(d.id);
        });
        usable.sort(function (a, b) {
          return (a.order || 0) - (b.order || 0);
        });
        usable.forEach(function (d) {
          const opt = document.createElement("option");
          opt.value = d.id;
          opt.textContent = d.id;
          select.appendChild(opt);
        });
        if (usable.length === 0 && status) {
          status.textContent = "No supported scene-based devices found.";
        }
      })
      .catch(function (err) {
        console.error("Failed to load devices", err);
        if (status) status.textContent = "Failed to load devices: " + err.message;
      });

    select.addEventListener("change", function () {
      renderBuilderForDevice(select.value);
    });
  }

  document.addEventListener("DOMContentLoaded", function () {
    populateDevicesDropdown();
  });
})();

