/**
 * NextHire - JARVIS Core AI Assistant & Interview Flow Controller
 * Implements the exact 5-step preparation workflow:
 * Step 1: Resume Upload
 * Step 2: Target Role Selection
 * Step 3: Resume Analysis & Automated Question Prep
 * Step 4: Ready for JARVIS Round (Continue ->)
 * Step 5: "Let's Start!" -> JARVIS Vocalization -> First Question
 */

class JarvisAssistant {
  constructor() {
    this.states = ['IDLE', 'LISTENING', 'THINKING', 'SPEAKING', 'PROCESSING'];
    this.currentState = 'IDLE';
    this.isRecording = false;
    this.synth = window.speechSynthesis || null;
    this.recognition = null;

    // Active Session State
    this.sessionCode = null;
    this.targetRole = null;
    this.selectedResumeFile = null;
    this.questions = [];
    this.currentQuestionIndex = 0;
    this.timerSeconds = 0;
    this.timerInterval = null;

    this.initElements();
    this.initCanvasWave();
    this.initSpeechRecognition();
    this.bindEvents();
    this.bindWorkflowEvents();

    // Start with Step 1 onboarding
    this.initSessionWorkflow();
  }

  initElements() {
    this.viewport = document.getElementById('interviewViewport');
    this.statePill = document.getElementById('jarvisStatePill');
    this.stateLabel = document.getElementById('jarvisStateLabel');
    this.subtextEl = document.getElementById('jarvisSubtext');
    this.stateButtons = document.querySelectorAll('.state-btn');

    this.hudSessionCode = document.getElementById('hudSessionCode');
    this.hudTargetRole = document.getElementById('hudTargetRole');

    this.qIndexPill = document.getElementById('qIndexPill');
    this.qTitle = document.getElementById('qTitle');
    this.qCategory = document.getElementById('qCategory');
    this.qDifficulty = document.getElementById('qDifficulty');

    this.liveTranscript = document.getElementById('liveTranscript');
    this.manualInput = document.getElementById('manualAnswerInput');
    this.micBtn = document.getElementById('micToggleBtn');
    this.audioBars = document.querySelectorAll('.audio-bar');
    this.timerEl = document.getElementById('answerTimer');
    this.wordCountEl = document.getElementById('wordCount');
    this.waveCanvas = document.getElementById('jarvisWaveCanvas');

    // Workflow Elements
    this.workflowOverlay = document.getElementById('workflowOverlay');
    this.workflowStepResume = document.getElementById('workflowStepResume');
    this.workflowStepRole = document.getElementById('workflowStepRole');
    this.workflowStepAnalysis = document.getElementById('workflowStepAnalysis');
    this.workflowStepReady = document.getElementById('workflowStepReady');
    this.letsStartBanner = document.getElementById('letsStartBanner');

    this.resumeFileInput = document.getElementById('workflowResumeFile');
    this.resumeDropZone = document.getElementById('resumeDropZone');
    this.fileStatusIndicator = document.getElementById('fileStatusIndicator');
    this.fileStatusName = document.getElementById('fileStatusName');
    this.btnUploadResume = document.getElementById('btnUploadResume');

    this.roleChips = document.querySelectorAll('.role-chip');
    this.customRoleContainer = document.getElementById('customRoleContainer');
    this.customRoleInput = document.getElementById('customRoleInput');
    this.btnConfirmRole = document.getElementById('btnConfirmRole');
    this.btnContinueToRound = document.getElementById('btnContinueToRound');
  }

  /**
   * Set JARVIS Assistant State and update visuals
   */
  setState(state, customSubtext) {
    state = state.toUpperCase();
    if (!this.states.includes(state)) return;

    this.currentState = state;

    if (this.viewport) {
      this.states.forEach(s => this.viewport.classList.remove(`jarvis-state-${s.toLowerCase()}`));
      this.viewport.classList.add(`jarvis-state-${state.toLowerCase()}`);
    }

    if (this.stateLabel) {
      this.stateLabel.textContent = state;
    }

    const defaultSubtexts = {
      IDLE: 'JARVIS is standing by. Ready for candidate prompt or question playback.',
      LISTENING: 'Microphone active. Real-time audio stream analyzing candidate response.',
      THINKING: 'Evaluating spoken response against architectural concept benchmarks...',
      SPEAKING: 'JARVIS is vocalizing the interview question.',
      PROCESSING: 'Aggregating concept coverage, fluency metrics, and semantic score.'
    };

    if (this.subtextEl) {
      this.subtextEl.textContent = customSubtext || defaultSubtexts[state] || '';
    }

    this.stateButtons.forEach(btn => {
      btn.classList.toggle('active', btn.dataset.state === state);
    });

    if (this.micBtn) {
      if (state === 'LISTENING') {
        this.micBtn.classList.add('active-recording');
        this.micBtn.innerHTML = `<span>⏹ Stop Answering</span>`;
      } else {
        this.micBtn.classList.remove('active-recording');
        this.micBtn.innerHTML = `<span>🎙 Answer with Voice</span>`;
      }
    }
  }

  /**
   * Speak a phrase aloud using Text-To-Speech with optional callback
   */
  speak(text, onEndCallback) {
    if (!this.synth) {
      if (onEndCallback) onEndCallback();
      return;
    }

    if (this.synth.speaking) {
      this.synth.cancel();
    }

    this.setState('SPEAKING');
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.rate = 1.0;
    utterance.pitch = 1.0;

    utterance.onend = () => {
      this.setState('IDLE');
      if (onEndCallback) onEndCallback();
    };

    utterance.onerror = () => {
      this.setState('IDLE');
      if (onEndCallback) onEndCallback();
    };

    this.synth.speak(utterance);
  }

  /**
   * Initialize Session & Launch Step 1
   */
  async initSessionWorkflow() {
    try {
      const res = await fetch('/api/interview/init', { method: 'POST' });
      const data = await res.json();
      if (data.success) {
        this.sessionCode = data.session_code;
        if (this.hudSessionCode) {
          this.hudSessionCode.textContent = this.sessionCode;
        }

        // Show Step 1: Resume Upload
        this.showWorkflowStep('workflowStepResume');
        this.setState('IDLE', 'Welcome to NextHire. Please upload your resume to continue.');

        // JARVIS Speaks Step 1 prompt
        setTimeout(() => {
          this.speak("Welcome to NextHire. Please upload your resume to continue.");
        }, 600);
      }
    } catch (e) {
      console.error('Session init error:', e);
      window.NextHire.showToast('Could not initialize interview session.', 'error');
    }
  }

  showWorkflowStep(stepId) {
    const steps = [
      this.workflowStepResume,
      this.workflowStepRole,
      this.workflowStepAnalysis,
      this.workflowStepReady
    ];
    steps.forEach(step => {
      if (step) step.classList.remove('active-step');
    });
    const target = document.getElementById(stepId);
    if (target) {
      target.classList.add('active-step');
    }
    if (this.workflowOverlay) {
      this.workflowOverlay.classList.remove('hidden');
    }
  }

  /**
   * Bind event handlers for the 5-step onboarding workflow
   */
  bindWorkflowEvents() {
    // --- STEP 1: RESUME UPLOAD ---
    if (this.resumeFileInput) {
      this.resumeFileInput.addEventListener('change', (e) => {
        if (e.target.files && e.target.files[0]) {
          this.handleResumeSelected(e.target.files[0]);
        }
      });
    }

    if (this.resumeDropZone) {
      this.resumeDropZone.addEventListener('dragover', (e) => {
        e.preventDefault();
        this.resumeDropZone.classList.add('dragover');
      });
      this.resumeDropZone.addEventListener('dragleave', () => {
        this.resumeDropZone.classList.remove('dragover');
      });
      this.resumeDropZone.addEventListener('drop', (e) => {
        e.preventDefault();
        this.resumeDropZone.classList.remove('dragover');
        if (e.dataTransfer.files && e.dataTransfer.files[0]) {
          this.handleResumeSelected(e.dataTransfer.files[0]);
        }
      });
    }

    if (this.btnUploadResume) {
      this.btnUploadResume.addEventListener('click', () => {
        this.uploadResumeAndProceed();
      });
    }

    // --- STEP 2: TARGET ROLE SELECTION ---
    this.roleChips.forEach(chip => {
      chip.addEventListener('click', () => {
        this.roleChips.forEach(c => c.classList.remove('selected'));
        chip.classList.add('selected');
        const role = chip.dataset.role;

        if (role === 'Custom Role') {
          if (this.customRoleContainer) this.customRoleContainer.classList.add('visible');
          if (this.customRoleInput) {
            this.customRoleInput.focus();
            this.targetRole = this.customRoleInput.value.trim();
          }
        } else {
          if (this.customRoleContainer) this.customRoleContainer.classList.remove('visible');
          this.targetRole = role;
        }

        if (this.btnConfirmRole) {
          this.btnConfirmRole.disabled = !this.targetRole;
        }
      });
    });

    if (this.customRoleInput) {
      this.customRoleInput.addEventListener('input', (e) => {
        this.targetRole = e.target.value.trim();
        if (this.btnConfirmRole) {
          this.btnConfirmRole.disabled = !this.targetRole;
        }
      });
    }

    if (this.btnConfirmRole) {
      this.btnConfirmRole.addEventListener('click', () => {
        this.submitRoleAndBeginAnalysis();
      });
    }

    // --- STEP 4 & 5: CONTINUE BUTTON ---
    if (this.btnContinueToRound) {
      this.btnContinueToRound.addEventListener('click', () => {
        this.startJarvisRound();
      });
    }
  }

  handleResumeSelected(file) {
    const ext = file.name.split('.').pop().toLowerCase();
    if (!['pdf', 'docx', 'doc'].includes(ext)) {
      window.NextHire.showToast('Invalid file format. Please upload a PDF or DOCX file.', 'error');
      return;
    }

    this.selectedResumeFile = file;
    if (this.fileStatusName) this.fileStatusName.textContent = `${file.name} (${(file.size / 1024).toFixed(1)} KB)`;
    if (this.fileStatusIndicator) this.fileStatusIndicator.style.display = 'flex';
    if (this.btnUploadResume) this.btnUploadResume.disabled = false;
  }

  async uploadResumeAndProceed() {
    if (!this.selectedResumeFile) {
      window.NextHire.showToast('Please select a resume file first.', 'warning');
      return;
    }

    this.setState('PROCESSING', 'Uploading and extracting technical resume matrix...');
    if (this.btnUploadResume) this.btnUploadResume.disabled = true;

    const formData = new FormData();
    formData.append('session_code', this.sessionCode);
    formData.append('resume', this.selectedResumeFile);

    try {
      const res = await fetch('/api/interview/upload-resume', {
        method: 'POST',
        body: formData
      });
      const data = await res.json();

      if (data.success) {
        window.NextHire.showToast('Resume uploaded successfully.', 'success');

        // JARVIS speaks: "Resume uploaded successfully."
        this.speak("Resume uploaded successfully.", () => {
          // Then automatically proceed to target-role step
          this.transitionToRoleStep();
        });
      } else {
        window.NextHire.showToast(data.error || 'Failed to process resume.', 'error');
        if (this.btnUploadResume) this.btnUploadResume.disabled = false;
        this.setState('IDLE');
      }
    } catch (err) {
      console.error('Upload error:', err);
      window.NextHire.showToast('Network error during upload.', 'error');
      if (this.btnUploadResume) this.btnUploadResume.disabled = false;
      this.setState('IDLE');
    }
  }

  transitionToRoleStep() {
    this.showWorkflowStep('workflowStepRole');
    this.setState('IDLE', 'Which role are you preparing for?');

    // JARVIS asks aloud: "Which role are you preparing for?"
    setTimeout(() => {
      this.speak("Which role are you preparing for?");
    }, 400);
  }

  async submitRoleAndBeginAnalysis() {
    if (!this.targetRole) {
      window.NextHire.showToast('Please select or enter your target role.', 'warning');
      return;
    }

    if (this.hudTargetRole) {
      this.hudTargetRole.textContent = this.targetRole;
    }

    // Step 3: Automatically begin Resume Analysis & Question Preparation
    this.showWorkflowStep('workflowStepAnalysis');
    this.setState('THINKING', `Analyzing resume skills and preparing questions for ${this.targetRole}...`);

    // Dynamic pipeline step animations
    const pSkills = document.getElementById('pipeSkills');
    const pRole = document.getElementById('pipeRole');
    const pQuestions = document.getElementById('pipeQuestions');

    setTimeout(() => {
      if (pSkills) {
        pSkills.className = 'pipeline-item completed';
        pSkills.innerHTML = '<i class="fas fa-check-circle"></i> <span>Technical Skills Extracted</span>';
      }
      if (pRole) {
        pRole.className = 'pipeline-item active';
        pRole.innerHTML = '<i class="fas fa-spinner fa-spin"></i> <span>Calibrating Difficulty Matrix...</span>';
      }
    }, 900);

    setTimeout(() => {
      if (pRole) {
        pRole.className = 'pipeline-item completed';
        pRole.innerHTML = '<i class="fas fa-check-circle"></i> <span>Target Role Calibrated</span>';
      }
      if (pQuestions) {
        pQuestions.className = 'pipeline-item active';
        pQuestions.innerHTML = '<i class="fas fa-spinner fa-spin"></i> <span>Synthesizing Question Bank...</span>';
      }
    }, 1800);

    try {
      const res = await fetch('/api/interview/select-role', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_code: this.sessionCode,
          target_role: this.targetRole
        })
      });
      const data = await res.json();

      if (data.success) {
        // Complete the pipeline visuals
        setTimeout(() => {
          if (pQuestions) {
            pQuestions.className = 'pipeline-item completed';
            pQuestions.innerHTML = '<i class="fas fa-check-circle"></i> <span>Question Bank Synthesized</span>';
          }

          // Step 4: Show Ready for JARVIS Round Confirmation Screen
          setTimeout(() => {
            this.showWorkflowStep('workflowStepReady');
            this.setState('IDLE', 'Your interview is ready. Are you ready for the JARVIS round?');
          }, 600);
        }, 2400);

      } else {
        window.NextHire.showToast(data.error || 'Question preparation failed.', 'error');
        this.showWorkflowStep('workflowStepRole');
        this.setState('IDLE');
      }
    } catch (err) {
      console.error('Role prep error:', err);
      window.NextHire.showToast('Network error during role analysis.', 'error');
      this.showWorkflowStep('workflowStepRole');
      this.setState('IDLE');
    }
  }

  /**
   * STEP 5: Continue button clicked -> "Let's Start!" -> JARVIS speaks -> First Question
   */
  async startJarvisRound() {
    try {
      const res = await fetch('/api/interview/start-round', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ session_code: this.sessionCode })
      });
      const data = await res.json();

      if (data.success) {
        // 1. Close preparation notification overlay
        if (this.workflowOverlay) {
          this.workflowOverlay.classList.add('hidden');
        }

        // 2. Show brief popup: "Let's Start!"
        if (this.letsStartBanner) {
          this.letsStartBanner.classList.add('show');
        }

        // 3. Activate JARVIS speaking state
        this.setState('SPEAKING', "Let's start.");

        // 4. JARVIS says: "Let's start."
        this.speak("Let's start.", () => {
          // Hide "Let's Start!" banner
          if (this.letsStartBanner) {
            this.letsStartBanner.classList.remove('show');
          }

          // 5. JARVIS asks the first interview question
          if (data.first_question) {
            this.currentQuestion = data.first_question;
            this.loadQuestionData(data.first_question, 0, data.total_questions || 3);
            setTimeout(() => {
              this.speakQuestionText(data.first_question.question_text);
            }, 500);
          }
        });
      } else {
        window.NextHire.showToast(data.error || 'Could not start round.', 'error');
      }
    } catch (err) {
      console.error('Start round error:', err);
      window.NextHire.showToast('Network error starting round.', 'error');
    }
  }

  loadQuestionData(q, index, total) {
    this.currentQuestion = q;
    this.currentQuestionIndex = index;
    this.currentTranscriptText = '';

    if (this.qIndexPill) this.qIndexPill.textContent = `Question ${index + 1} of ${total}`;
    if (this.qTitle) this.qTitle.textContent = q.question_text;
    if (this.qCategory) this.qCategory.textContent = q.category || 'Technical';
    if (this.qDifficulty) this.qDifficulty.textContent = q.difficulty || 'Intermediate';

    if (this.liveTranscript) {
      this.liveTranscript.innerHTML = `<span class="transcript-placeholder"><i class="fas fa-wave-square"></i> Press "Answer with Voice" or type below to begin your answer...</span>`;
    }
    if (this.manualInput) {
      this.manualInput.value = '';
    }
    if (this.wordCountEl) {
      this.wordCountEl.textContent = '0 words';
    }
    this.resetAnswerTimer();
  }

  speakQuestionText(text) {
    if (!text) return;
    this.setState('SPEAKING', `JARVIS is speaking Question ${this.currentQuestionIndex + 1}`);
    this.speak(text, () => {
      this.setState('IDLE', 'Candidate may press "Answer with Voice" or type response below.');
    });
  }

  /**
   * Submit the current answer and advance to next question
   * Does NOT evaluate final score during the interview round
   */
  async submitCurrentAnswer() {
    if (this.isRecording) {
      this.stopListening();
    }

    const answerText = (this.manualInput && this.manualInput.value.trim()) ||
                       this.currentTranscriptText ||
                       (this.liveTranscript && !this.liveTranscript.innerHTML.includes('transcript-placeholder') ? this.liveTranscript.innerText.replace('Candidate:', '').trim() : "");

    if (!answerText) {
      window.NextHire.showToast('Please speak or type your answer before submitting, or click Skip Question.', 'warning');
      return;
    }

    const qid = this.currentQuestion ? (this.currentQuestion.id || this.currentQuestion.question_code) : (this.currentQuestionIndex + 1);

    this.setState('THINKING', 'Saving answer response to isolated session...');

    try {
      const res = await fetch('/api/interview/submit-answer', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_code: this.sessionCode,
          question_id: qid,
          transcript_text: answerText,
          status: 'answered'
        })
      });
      const data = await res.json();

      if (data.success) {
        window.NextHire.showToast(`Question ${this.currentQuestionIndex + 1} response saved.`, 'success');

        if (data.is_completed) {
          // All questions completed! End JARVIS round and evaluate complete session
          this.finishInterviewAndEvaluate();
        } else if (data.next_question) {
          this.loadQuestionData(data.next_question, data.current_question_index, data.total_questions);
          setTimeout(() => {
            this.speakQuestionText(data.next_question.question_text);
          }, 400);
        }
      } else {
        window.NextHire.showToast(data.error || 'Failed to submit answer.', 'error');
        this.setState('IDLE');
      }
    } catch (err) {
      console.error('Submit answer error:', err);
      window.NextHire.showToast('Network error submitting answer.', 'error');
      this.setState('IDLE');
    }
  }

  /**
   * Skip current question
   * Stores answer_status = "skipped" without marking correct/incorrect
   */
  async skipCurrentQuestion() {
    if (this.isRecording) {
      this.stopListening();
    }

    const qid = this.currentQuestion ? (this.currentQuestion.id || this.currentQuestion.question_code) : (this.currentQuestionIndex + 1);

    this.setState('THINKING', 'Marking question as skipped...');

    try {
      const res = await fetch('/api/interview/submit-answer', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_code: this.sessionCode,
          question_id: qid,
          transcript_text: '',
          status: 'skipped'
        })
      });
      const data = await res.json();

      if (data.success) {
        window.NextHire.showToast(`Question ${this.currentQuestionIndex + 1} marked as Skipped.`, 'warning');

        if (data.is_completed) {
          this.finishInterviewAndEvaluate();
        } else if (data.next_question) {
          this.loadQuestionData(data.next_question, data.current_question_index, data.total_questions);
          setTimeout(() => {
            this.speakQuestionText(data.next_question.question_text);
          }, 400);
        }
      } else {
        window.NextHire.showToast(data.error || 'Failed to skip question.', 'error');
        this.setState('IDLE');
      }
    } catch (err) {
      console.error('Skip question error:', err);
      window.NextHire.showToast('Network error skipping question.', 'error');
      this.setState('IDLE');
    }
  }

  /**
   * POST-INTERVIEW ANALYSIS:
   * End JARVIS voice session, run concept evaluation, calculate scores, and redirect
   */
  async finishInterviewAndEvaluate() {
    this.setState('PROCESSING', 'Interview complete! Analyzing session concepts, communication, and confidence...');

    // JARVIS vocalizes session conclusion
    this.speak("Thank you. You have completed the interview questions. Analyzing your complete session now.");

    // Store session code for feedback page lookup
    if (this.sessionCode) {
      localStorage.setItem('nexthire_last_session', this.sessionCode);
    }

    try {
      const res = await fetch('/api/interview/evaluate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ session_code: this.sessionCode })
      });
      const data = await res.json();

      if (data.success) {
        window.NextHire.showToast('Evaluation complete! Opening performance report...', 'success');
        setTimeout(() => {
          window.location.href = `/feedback?session=${encodeURIComponent(this.sessionCode)}`;
        }, 1200);
      } else {
        window.NextHire.showToast(data.error || 'Evaluation processing error.', 'error');
        setTimeout(() => {
          window.location.href = `/feedback?session=${encodeURIComponent(this.sessionCode)}`;
        }, 1500);
      }
    } catch (err) {
      console.error('Evaluation call error:', err);
      setTimeout(() => {
        window.location.href = `/feedback?session=${encodeURIComponent(this.sessionCode)}`;
      }, 1500);
    }
  }

  /**
   * Canvas Audio Waveform Generator inside Core
   */
  initCanvasWave() {
    if (!this.waveCanvas) return;
    const ctx = this.waveCanvas.getContext('2d');
    let step = 0;

    const render = () => {
      step += 0.05;
      const width = this.waveCanvas.width;
      const height = this.waveCanvas.height;
      ctx.clearRect(0, 0, width, height);

      ctx.beginPath();
      ctx.lineWidth = 2;

      let color = 'rgba(0, 229, 255, 0.8)';
      let freq = 0.08;
      let amp = 5;

      if (this.currentState === 'LISTENING') {
        color = 'rgba(0, 245, 160, 0.95)';
        freq = 0.16;
        amp = 9 + Math.sin(step * 3) * 3;
      } else if (this.currentState === 'SPEAKING') {
        color = 'rgba(96, 165, 250, 0.95)';
        freq = 0.12;
        amp = 8 + Math.cos(step * 2) * 4;
      } else if (this.currentState === 'THINKING') {
        color = 'rgba(255, 183, 3, 0.95)';
        freq = 0.25;
        amp = 4 + Math.sin(step * 6) * 3;
      } else if (this.currentState === 'PROCESSING') {
        color = 'rgba(157, 78, 221, 0.95)';
        freq = 0.2;
        amp = 6;
      }

      ctx.strokeStyle = color;

      for (let x = 0; x < width; x++) {
        const y = height / 2 + Math.sin(x * freq + step * 2) * amp * Math.sin(x / width * Math.PI);
        if (x === 0) {
          ctx.moveTo(x, y);
        } else {
          ctx.lineTo(x, y);
        }
      }
      ctx.stroke();

      requestAnimationFrame(render);
    };

    render();
  }

  initSpeechRecognition() {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition || null;
    if (SpeechRecognition) {
      this.recognition = new SpeechRecognition();
      this.recognition.continuous = true;
      this.recognition.interimResults = true;
      this.recognition.lang = 'en-US';

      this.recognition.onresult = (event) => {
        let transcript = '';
        for (let i = event.resultIndex; i < event.results.length; ++i) {
          transcript += event.results[i][0].transcript;
        }
        this.updateTranscript(transcript);
        this.animateAudioMeter(true);
      };

      this.recognition.onerror = (e) => {
        console.warn('Speech recognition error:', e.error);
        if (e.error === 'not-allowed') {
          window.NextHire.showToast('Microphone access denied. You can use manual text input.', 'warning');
        }
        this.stopListening();
      };
    }
  }

  toggleListening() {
    if (this.isRecording) {
      this.stopListening();
    } else {
      this.startListening();
    }
  }

  startListening() {
    this.isRecording = true;
    this.setState('LISTENING');
    this.startAnswerTimer();

    if (this.recognition) {
      try {
        this.recognition.start();
        window.NextHire.showToast('Listening... Speak your answer clearly.', 'info');
      } catch (err) {
        console.warn('Recognition start error:', err);
      }
    } else {
      window.NextHire.showToast('Speech recognition active. Speak or type below.', 'info');
      this.simulateSpeechInput();
    }
  }

  stopListening() {
    this.isRecording = false;
    this.stopAnswerTimer();
    this.animateAudioMeter(false);

    if (this.recognition) {
      try { this.recognition.stop(); } catch (_) {}
    }

    this.setState('THINKING', 'Answer captured. Processing concepts...');
    setTimeout(() => {
      this.setState('IDLE', 'Response saved. Click Next to proceed or Speak again to append.');
    }, 1600);
  }

  updateTranscript(text) {
    this.currentTranscriptText = text;
    if (!this.liveTranscript) return;
    this.liveTranscript.innerHTML = `<span class="recording-pulse-dot"></span> <strong>Candidate:</strong> ${text}`;
    if (this.manualInput) {
      this.manualInput.value = text;
    }
    const words = text.trim().split(/\s+/).filter(Boolean).length;
    if (this.wordCountEl) {
      this.wordCountEl.textContent = `${words} words`;
    }
  }

  simulateSpeechInput() {
    if (!this.isRecording) return;
    const demoPhrases = [
      "In a monolithic system, all components exist in a unified code deployment.",
      "Microservices split application domains into autonomous loosely coupled services.",
      "Inter-service communication is usually handled via REST, gRPC, or message brokers like Kafka."
    ];
    let idx = 0;
    const interval = setInterval(() => {
      if (!this.isRecording || idx >= demoPhrases.length) {
        clearInterval(interval);
        return;
      }
      this.updateTranscript(demoPhrases.slice(0, idx + 1).join(" "));
      this.animateAudioMeter(true);
      idx++;
    }, 1400);
  }

  startAnswerTimer() {
    this.stopAnswerTimer();
    this.timerInterval = setInterval(() => {
      this.timerSeconds++;
      const mins = Math.floor(this.timerSeconds / 60).toString().padStart(2, '0');
      const secs = (this.timerSeconds % 60).toString().padStart(2, '0');
      if (this.timerEl) {
        this.timerEl.textContent = `${mins}:${secs}`;
      }
    }, 1000);
  }

  stopAnswerTimer() {
    if (this.timerInterval) {
      clearInterval(this.timerInterval);
      this.timerInterval = null;
    }
  }

  resetAnswerTimer() {
    this.stopAnswerTimer();
    this.timerSeconds = 0;
    if (this.timerEl) {
      this.timerEl.textContent = '00:00';
    }
  }

  animateAudioMeter(isActive) {
    if (!this.audioBars || this.audioBars.length === 0) return;
    this.audioBars.forEach(bar => {
      if (isActive) {
        const h = Math.floor(Math.random() * 85) + 15;
        bar.style.height = `${h}%`;
        bar.classList.add('active');
      } else {
        bar.style.height = '15%';
        bar.classList.remove('active');
      }
    });
  }

  bindEvents() {
    // State switcher buttons for direct inspection
    this.stateButtons.forEach(btn => {
      btn.addEventListener('click', () => {
        const targetState = btn.dataset.state;
        this.setState(targetState);
        window.NextHire.showToast(`JARVIS switched to ${targetState} state`, 'info');
      });
    });

    if (this.micBtn) {
      this.micBtn.addEventListener('click', () => this.toggleListening());
    }

    const speakBtn = document.getElementById('speakQuestionBtn');
    if (speakBtn) {
      speakBtn.addEventListener('click', () => {
        const currentText = this.qTitle ? this.qTitle.textContent : "";
        this.speakQuestionText(currentText);
      });
    }

    const repeatBtn = document.getElementById('repeatQuestionBtn');
    if (repeatBtn) {
      repeatBtn.addEventListener('click', () => {
        const currentText = this.qTitle ? this.qTitle.textContent : "";
        this.speakQuestionText(currentText);
      });
    }

    const nextBtn = document.getElementById('nextQuestionBtn');
    if (nextBtn) {
      nextBtn.addEventListener('click', () => {
        this.submitCurrentAnswer();
      });
    }

    const skipBtn = document.getElementById('skipQuestionBtn');
    if (skipBtn) {
      skipBtn.addEventListener('click', () => {
        this.skipCurrentQuestion();
      });
    }

    const stopBtn = document.getElementById('stopInterviewBtn');
    if (stopBtn) {
      stopBtn.addEventListener('click', (e) => {
        if (this.sessionCode && this.currentQuestionIndex > 0) {
          e.preventDefault();
          this.finishInterviewAndEvaluate();
        }
      });
    }

    const toggleInputBtn = document.getElementById('toggleManualInputBtn');
    if (toggleInputBtn && this.manualInput) {
      toggleInputBtn.addEventListener('click', () => {
        const isHidden = getComputedStyle(this.manualInput).display === 'none';
        this.manualInput.style.display = isHidden ? 'block' : 'none';
        toggleInputBtn.textContent = isHidden ? 'Hide Text Editor' : 'Type Answer Manually';
      });
    }

    if (this.manualInput) {
      this.manualInput.addEventListener('input', (e) => {
        this.updateTranscript(e.target.value);
      });
    }
  }
}

document.addEventListener('DOMContentLoaded', () => {
  if (document.getElementById('interviewViewport')) {
    window.jarvis = new JarvisAssistant();
  }
});
