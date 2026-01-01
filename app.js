// Stoicism Presentation App
class PresentationApp {
    constructor() {
        this.currentSlide = 0;
        this.slides = [];
        this.data = null;
        this.touchStartX = 0;
        this.touchEndX = 0;
        this.autoPlayInterval = null;
        this.autoPlayDelay = 5000; // 5 seconds

        this.init();
    }

    async init() {
        try {
            await this.loadData();
            this.renderSlides();
            this.setupEventListeners();
            this.updateUI();
            this.setupOverview();
        } catch (error) {
            console.error('Failed to initialize app:', error);
            document.getElementById('slide-container').innerHTML = `
                <div style="text-align: center; padding: 2rem;">
                    <p style="color: #C49A6C; font-size: 1.5rem;">Error loading presentation</p>
                    <p style="margin-top: 1rem;">Please make sure presentation_data.json is available.</p>
                </div>
            `;
        }
    }

    async loadData() {
        try {
            // Add cache-busting parameter
            const cacheBuster = new Date().getTime();
            const response = await fetch(`presentation_data.json?v=${cacheBuster}`, {
                cache: 'no-cache',
                headers: {
                    'Cache-Control': 'no-cache',
                    'Pragma': 'no-cache'
                }
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const text = await response.text();
            this.data = JSON.parse(text);

            if (!this.data || !this.data.slides) {
                throw new Error('Invalid presentation data structure');
            }

            this.slides = this.data.slides;
            console.log(`✓ Successfully loaded ${this.slides.length} slides from presentation_data.json`);
        } catch (error) {
            console.error('✗ Error loading presentation data:', error);
            throw error;
        }
    }

    renderSlides() {
        const container = document.getElementById('slide-container');
        container.innerHTML = '';

        // Add navigation arrows
        container.innerHTML += `
            <button class="nav-arrow left" id="prev-btn" title="Previous (←)">
                <i class="fas fa-chevron-left"></i>
            </button>
            <button class="nav-arrow right" id="next-btn" title="Next (→)">
                <i class="fas fa-chevron-right"></i>
            </button>
        `;

        this.slides.forEach((slide, index) => {
            const slideEl = document.createElement('div');
            slideEl.className = `slide ${slide.type}${index === 0 ? ' active' : ''}`;
            slideEl.innerHTML = this.renderSlideContent(slide);
            container.appendChild(slideEl);
        });

        document.getElementById('total-slides').textContent = this.slides.length;
    }

    renderSlideContent(slide) {
        switch (slide.type) {
            case 'cover':
                return this.renderCoverSlide(slide);
            case 'table_of_contents':
                return this.renderTOCSlide(slide);
            case 'chapter':
                return this.renderChapterSlide(slide);
            case 'final':
                return this.renderFinalSlide(slide);
            default:
                return this.renderContentSlide(slide);
        }
    }

    renderCoverSlide(slide) {
        return `
            <h1 class="font-display">${slide.title}</h1>
            <div class="subtitle font-heading">${slide.subtitle}</div>
            <div class="divider"></div>
            <p class="tagline">${slide.tagline}</p>
        `;
    }

    renderTOCSlide(slide) {
        const sections = slide.sections.map((section, i) => `
            <div class="card" style="border-left-color: ${section.color}">
                <div style="display: flex; align-items: start; gap: 1.5rem;">
                    <div class="card-icon" style="background: ${section.color}; flex-shrink: 0;">
                        <span class="font-display" style="color: #2B2B2B; font-size: 1.5rem; font-weight: bold;">${section.number}</span>
                    </div>
                    <div>
                        <h3 class="font-heading">${section.title}</h3>
                        <p style="color: var(--accent);">${section.description}</p>
                    </div>
                </div>
            </div>
        `).join('');

        return `
            <h2 class="font-display">${slide.title}</h2>
            <div class="divider"></div>
            <div style="margin-top: 2rem;">
                ${sections}
            </div>
        `;
    }

    renderChapterSlide(slide) {
        return `
            <div style="height: 100%; display: flex; flex-direction: column; justify-content: center;">
                <div style="font-size: 6rem; font-weight: bold; color: var(--primary); margin-bottom: 2rem;" class="font-display">
                    ${slide.chapterNumber}
                </div>
                <h1 class="font-heading" style="font-size: 4rem; margin-bottom: 1rem;">${slide.title}</h1>
                <div class="divider"></div>
                ${slide.subtitle ? `<p style="font-size: 1.5rem; color: var(--accent); margin-top: 1rem;">${slide.subtitle}</p>` : ''}
            </div>
        `;
    }

    renderFinalSlide(slide) {
        // Handle content being an object or array
        const content = slide.content || {};
        const icon = content.icon || slide.icon;
        const messages = content.messages || (Array.isArray(content) ? content : []);
        const quote = content.quote || slide.quote;
        const virtues = content.virtues || slide.virtues || [];

        const cards = virtues.map(virtue => `
            <div class="card" style="text-align: center;">
                <i class="fas ${virtue.icon}" style="font-size: 2rem; color: var(--primary); margin-bottom: 0.5rem;"></i>
                <p style="font-weight: bold;">${virtue.name}</p>
            </div>
        `).join('');

        return `
            <div style="text-align: center; max-width: 900px; margin: 0 auto;">
                ${icon ? `<i class="fas ${icon}" style="font-size: 4rem; color: var(--primary); margin-bottom: 2rem;"></i>` : ''}
                <h2 class="font-heading" style="font-size: 3.5rem; margin-bottom: 1.5rem;">${slide.title}</h2>
                <div class="divider" style="margin: 1.5rem auto;"></div>
                ${messages.length > 0 ? messages.map(p => `<p style="font-size: 1.2rem; margin-bottom: 1.5rem;">${p}</p>`).join('') : ''}
                ${quote ? `
                    <div class="quote" style="margin: 2rem 0;">
                        <p style="font-size: 1.3rem;">"${quote.text}"</p>
                        <p class="quote-author">— ${quote.author}</p>
                    </div>
                ` : ''}
                ${cards ? `<div class="grid-4">${cards}</div>` : ''}
            </div>
        `;
    }

    renderContentSlide(slide) {
        let html = `
            <h2 class="font-display">${slide.title}</h2>
            ${slide.subtitle ? `<p style="font-size: 1.2rem; color: var(--accent); margin-bottom: 1rem;">${slide.subtitle}</p>` : ''}
            <div class="divider"></div>
        `;

        // Handle different content structures
        if (slide.sections) {
            html += this.renderSections(slide.sections);
        } else if (slide.content) {
            html += this.renderContent(slide.content);
        } else if (slide.cards) {
            html += this.renderCards(slide.cards);
        } else if (slide.timeline) {
            html += this.renderTimeline(slide.timeline);
        } else if (slide.grid) {
            html += this.renderGrid(slide.grid);
        }

        // Add closing note if exists
        if (slide.note) {
            html += `
                <div class="card" style="margin-top: 1.5rem; background: rgba(196, 154, 108, 0.1);">
                    <p><strong>${slide.note.title || 'Note'}:</strong> ${slide.note.text}</p>
                </div>
            `;
        }

        return html;
    }

    renderSections(sections) {
        return sections.map(section => {
            let content = '';

            if (section.text) {
                content += `<p>${section.text}</p>`;
            }

            if (section.points) {
                content += '<ul>' + section.points.map(p => `<li>${p}</li>`).join('') + '</ul>';
            }

            if (section.quote) {
                content += `
                    <div class="quote">
                        <p>"${section.quote.text}"</p>
                        ${section.quote.author ? `<p class="quote-author">— ${section.quote.author}</p>` : ''}
                    </div>
                `;
            }

            if (section.subsections) {
                content += section.subsections.map(sub => `
                    <div style="margin: 1rem 0;">
                        <h4>${sub.title}</h4>
                        <p>${sub.text}</p>
                    </div>
                `).join('');
            }

            return `
                <div style="margin: 1.5rem 0;">
                    ${section.title ? `<h3 class="font-heading">${section.title}</h3>` : ''}
                    ${content}
                </div>
            `;
        }).join('');
    }

    renderContent(content) {
        if (typeof content === 'string') {
            return `<p>${content}</p>`;
        }

        if (Array.isArray(content)) {
            return content.map(item => {
                if (typeof item === 'string') {
                    return `<p>${item}</p>`;
                }
                return '';
            }).join('');
        }

        // Handle object content with nested structures
        if (typeof content === 'object' && content !== null) {
            let html = '';

            // Timeline
            if (content.timeline) {
                html += this.renderTimeline(content.timeline);
            }

            // Cards
            if (content.cards) {
                html += this.renderCards(content.cards);
            }

            // Grid
            if (content.grid) {
                html += this.renderGrid(content.grid);
            }

            // Sections
            if (content.sections) {
                html += this.renderSections(content.sections);
            }

            // Main sections (like in "What is Stoicism")
            if (content.mainSections) {
                html += this.renderMainSections(content.mainSections);
            }

            // Quote
            if (content.quote && !content.mainSections) {
                html += `<div class="quote" style="margin: 2rem 0;">
                    <p style="font-size: 1.2rem;">"${content.quote.text}"</p>
                    ${content.quote.author ? `<p class="quote-author">— ${content.quote.author}</p>` : ''}
                </div>`;
            }

            // Key principles
            if (content.keyPrinciples) {
                html += this.renderKeyPrinciples(content.keyPrinciples);
            }

            // Virtues (for Four Cardinal Virtues slide)
            if (content.virtues) {
                html += this.renderVirtuesContent(content.virtues);
                if (content.unityNote) {
                    // Handle unityNote as either string or object
                    const note = typeof content.unityNote === 'string'
                        ? { text: content.unityNote }
                        : content.unityNote;
                    html += `<div class="card" style="margin-top: 2rem; background: rgba(196, 154, 108, 0.1);">
                        <p style="text-align: center;">${note.title ? `<strong>${note.title}:</strong> ` : ''}${note.text}</p>
                    </div>`;
                }
            }

            // Dichotomy of Control structure
            if (content.epictetus) {
                html += this.renderDichotomy(content);
            }

            // Teachers
            if (content.teachers) {
                html += this.renderTeachers(content.teachers);
            }

            // Digital Stoicism dichotomy (slide 17)
            if (content.dichotomyOnline) {
                html += this.renderDigitalDichotomy(content.dichotomyOnline);
            }

            // Complex content structures (exercises, practices, etc.)
            if (content.whatItIs || content.definition || content.modernChallenge || content.directLineage || content.sabs || content.morning || content.evening) {
                html += this.renderComplexContent(content);
            }

            return html;
        }

        return '';
    }

    renderCards(cards) {
        const gridClass = cards.length === 4 ? 'grid-4' : 'grid-2';
        return `
            <div class="${gridClass}">
                ${cards.map(card => `
                    <div class="card ${card.color === 'secondary' ? 'secondary' : ''}">
                        ${card.icon ? `
                            <div class="card-icon ${card.color === 'secondary' ? 'secondary' : ''}">
                                <i class="${card.icon}"></i>
                            </div>
                        ` : ''}
                        <h4>${card.title}</h4>
                        ${card.subtitle ? `<p style="color: var(--primary); margin-bottom: 0.5rem;"><strong>${card.subtitle}</strong></p>` : ''}
                        ${card.text ? `<p style="color: var(--accent);">${card.text}</p>` : ''}
                        ${card.practice ? `
                            <div style="background: rgba(43, 43, 43, 0.6); padding: 0.75rem; border-radius: 4px; margin-top: 0.75rem;">
                                <p style="font-size: 0.9rem;"><strong>Practice:</strong> ${card.practice}</p>
                            </div>
                        ` : ''}
                    </div>
                `).join('')}
            </div>
        `;
    }

    renderTimeline(timeline) {
        return `
            <div style="margin: 2rem 0;">
                ${timeline.map((item, i) => `
                    <div style="display: flex; gap: 1.5rem; margin-bottom: 2rem; padding: 1.5rem; background: rgba(58, 58, 58, 0.4); border-radius: 8px; border-left: 4px solid ${item.color || 'var(--primary)'};">
                        <div style="flex-shrink: 0; text-align: center; min-width: 120px;">
                            <div style="font-size: 1.2rem; font-weight: bold; color: var(--primary); margin-bottom: 0.5rem;">${item.period}</div>
                        </div>
                        <div style="flex: 1;">
                            <h3 style="font-size: 1.4rem; margin-bottom: 0.5rem; color: var(--primary);">${item.name || item.title}</h3>
                            ${item.role ? `<p style="font-style: italic; color: var(--accent); margin-bottom: 0.75rem;">${item.role}</p>` : ''}
                            <p style="color: var(--text); margin-bottom: 0.75rem;">${item.description}</p>
                            ${item.keyInsight ? `<p style="font-style: italic; color: var(--primary); padding: 0.75rem; background: rgba(196, 154, 108, 0.1); border-radius: 4px; margin-top: 0.75rem;"><strong>Key Insight:</strong> "${item.keyInsight}"</p>` : ''}
                        </div>
                    </div>
                `).join('')}
            </div>
        `;
    }

    renderGrid(grid) {
        return `
            <div class="grid-2">
                ${grid.map(item => `
                    <div class="card">
                        <h4 style="color: var(--primary); margin-bottom: 0.75rem;">${item.title}</h4>
                        ${item.items ? `
                            <ul>
                                ${item.items.map(i => `<li>${i}</li>`).join('')}
                            </ul>
                        ` : ''}
                        ${item.text ? `<p>${item.text}</p>` : ''}
                    </div>
                `).join('')}
            </div>
        `;
    }

    renderMainSections(sections) {
        return `
            <div class="grid-2" style="margin: 2rem 0;">
                ${sections.map(section => `
                    <div class="card" style="border-left-color: ${section.color || 'var(--primary)'}">
                        ${section.icon ? `<div class="card-icon" style="background: ${section.color || 'var(--primary)'}"><i class="fas ${section.icon}"></i></div>` : ''}
                        <h3 style="color: var(--primary); margin-bottom: 1rem;">${section.heading}</h3>
                        ${Array.isArray(section.text) ? section.text.map(p => `<p style="margin-bottom: 0.75rem;">${p}</p>`).join('') : `<p>${section.text}</p>`}
                    </div>
                `).join('')}
            </div>
        `;
    }

    renderKeyPrinciples(principles) {
        // Handle both array and object formats
        const items = Array.isArray(principles) ? principles : (principles.items || []);
        const title = Array.isArray(principles) ? 'Key Principles' : (principles.title || 'Key Principles');

        return `
            <div style="margin-top: 2rem;">
                <h3 style="color: var(--primary); margin-bottom: 1rem; font-size: 1.5rem;">${title}</h3>
                <div class="grid-2">
                    ${items.map(item => `
                        <div class="card secondary">
                            <h4 style="color: var(--primary);">${item.title}</h4>
                            <p>${item.description}</p>
                        </div>
                    `).join('')}
                </div>
            </div>
        `;
    }

    renderVirtuesContent(virtues) {
        return `
            <div class="grid-2" style="margin: 2rem 0;">
                ${virtues.map(virtue => `
                    <div class="card" style="border-left-color: ${virtue.color || 'var(--primary)'}">
                        <div style="display: flex; align-items: center; gap: 1rem; margin-bottom: 0.75rem;">
                            <div class="card-icon" style="background: ${virtue.color || 'var(--primary)'}; width: 40px; height: 40px; margin: 0;">
                                <i class="fas ${virtue.icon}" style="font-size: 1.2rem;"></i>
                            </div>
                            <h3 style="color: var(--primary); margin: 0;">${virtue.name}</h3>
                        </div>
                        <p style="font-weight: bold; color: var(--primary); margin-bottom: 0.5rem;">${virtue.subtitle}</p>
                        <p style="margin-bottom: 0.75rem;">${virtue.description}</p>
                        <div style="background: rgba(43, 43, 43, 0.6); padding: 0.75rem; border-radius: 4px;">
                            <p style="font-size: 0.9rem;"><strong>Practice:</strong> ${virtue.practice}</p>
                        </div>
                    </div>
                `).join('')}
            </div>
        `;
    }

    renderDichotomy(content) {
        return `
            <div style="margin: 2rem 0;">
                <div class="quote" style="margin-bottom: 2rem;">
                    <p style="font-size: 1.3rem; font-style: italic;">"${content.epictetus.quote}"</p>
                    <p style="margin-top: 1rem;">${content.epictetus.explanation}</p>
                </div>
                <div class="grid-2">
                    <div class="card" style="border-left-color: ${content.withinControl.color};">
                        <h3 style="color: var(--primary); margin-bottom: 1rem;">${content.withinControl.title}</h3>
                        <ul style="margin-bottom: 1rem;">
                            ${content.withinControl.items.map(item => `
                                <li style="margin-bottom: 0.5rem;">
                                    <strong>${item.item}:</strong> ${item.description}
                                </li>
                            `).join('')}
                        </ul>
                        <p style="font-style: italic; color: var(--primary);">${content.withinControl.summary}</p>
                    </div>
                    <div class="card" style="border-left-color: ${content.beyondControl.color};">
                        <h3 style="color: var(--accent); margin-bottom: 1rem;">${content.beyondControl.title}</h3>
                        <ul style="margin-bottom: 1rem;">
                            ${content.beyondControl.items.map(item => `
                                <li style="margin-bottom: 0.5rem;">
                                    <strong>${item.item}:</strong> ${item.description}
                                </li>
                            `).join('')}
                        </ul>
                        <p style="font-style: italic; color: var(--accent);">${content.beyondControl.summary}</p>
                    </div>
                </div>
                ${content.practice ? `
                    <div class="card" style="margin-top: 2rem; background: rgba(196, 154, 108, 0.1);">
                        ${Array.isArray(content.practice) ? `
                            <h4 style="color: var(--primary); margin-bottom: 1rem;">Practice</h4>
                            ${content.practice.map(step => `
                                <div style="margin-bottom: 1rem;">
                                    <strong>Step ${step.step}:</strong> ${step.description}
                                </div>
                            `).join('')}
                        ` : `
                            <h4 style="color: var(--primary);">${content.practice.title}</h4>
                            <p>${content.practice.description}</p>
                        `}
                    </div>
                ` : ''}
            </div>
        `;
    }

    renderTeachers(teachers) {
        return `
            <div class="grid-2" style="margin: 2rem 0;">
                ${teachers.map(teacher => `
                    <div class="card" style="border-left-color: ${teacher.color || 'var(--primary)'}">
                        <h3 style="color: var(--primary); margin-bottom: 0.5rem;">${teacher.name}</h3>
                        <p style="font-style: italic; color: var(--accent); margin-bottom: 0.75rem;">${teacher.role}</p>
                        <p style="margin-bottom: 0.75rem;">${teacher.description}</p>
                        ${teacher.quote ? `
                            <div style="background: rgba(196, 154, 108, 0.1); padding: 0.75rem; border-radius: 4px; margin-bottom: 0.75rem;">
                                <p style="font-size: 0.95rem; font-style: italic;">"${teacher.quote}"</p>
                            </div>
                        ` : ''}
                        ${teacher.inspiration ? `
                            <div style="background: rgba(196, 154, 108, 0.1); padding: 0.75rem; border-radius: 4px;">
                                <p style="font-size: 0.95rem;"><strong>Inspiration:</strong> "${teacher.inspiration}"</p>
                            </div>
                        ` : ''}
                        ${teacher.keyWorks ? `
                            <div style="margin-top: 0.75rem;">
                                <p style="font-size: 0.9rem; font-weight: bold; color: var(--primary); margin-bottom: 0.5rem;">Key Works:</p>
                                ${teacher.keyWorks.map(work => `
                                    <div style="margin-bottom: 0.5rem; padding-left: 1rem;">
                                        <p style="font-size: 0.9rem;"><strong>${work.title}:</strong> ${work.description}</p>
                                    </div>
                                `).join('')}
                            </div>
                        ` : ''}
                        ${teacher.coreTeachings ? `
                            <div style="margin-top: 0.75rem;">
                                <p style="font-size: 0.9rem; font-weight: bold; color: var(--primary); margin-bottom: 0.5rem;">Core Teachings:</p>
                                <ul style="font-size: 0.9rem;">
                                    ${teacher.coreTeachings.map(teaching => `<li>${teaching}</li>`).join('')}
                                </ul>
                            </div>
                        ` : ''}
                        ${teacher.coreThemes ? `
                            <div style="margin-top: 0.75rem;">
                                <p style="font-size: 0.9rem; font-weight: bold; color: var(--primary); margin-bottom: 0.5rem;">Core Themes:</p>
                                <ul style="font-size: 0.9rem;">
                                    ${teacher.coreThemes.map(theme => `<li>${theme}</li>`).join('')}
                                </ul>
                            </div>
                        ` : ''}
                    </div>
                `).join('')}
            </div>
        `;
    }

    renderDigitalDichotomy(dichotomy) {
        return `
            <div style="margin: 2rem 0;">
                <h3 style="color: var(--primary); margin-bottom: 1.5rem; font-size: 1.5rem;">${dichotomy.title}</h3>
                <div class="grid-2">
                    <div class="card" style="border-left-color: var(--accent);">
                        <h4 style="color: var(--accent); margin-bottom: 1rem;">Beyond Our Control</h4>
                        <ul>
                            ${dichotomy.beyondControl.map(item => `<li>${item}</li>`).join('')}
                        </ul>
                    </div>
                    <div class="card" style="border-left-color: var(--primary);">
                        <h4 style="color: var(--primary); margin-bottom: 1rem;">Within Our Control</h4>
                        <ul>
                            ${dichotomy.withinControl.map(item => `<li>${item}</li>`).join('')}
                        </ul>
                    </div>
                </div>
                ${dichotomy.keyInsight ? `
                    <div class="card" style="margin-top: 2rem; background: rgba(196, 154, 108, 0.1);">
                        <p style="font-style: italic; text-align: center;">${dichotomy.keyInsight}</p>
                    </div>
                ` : ''}
            </div>
        `;
    }

    renderComplexContent(content) {
        let html = '';

        // Render all text-based properties
        Object.keys(content).forEach(key => {
            const value = content[key];

            if (typeof value === 'object' && value !== null && !Array.isArray(value)) {
                // Morning/Evening routines (slide 11)
                if ((key === 'morning' || key === 'evening') && value.steps) {
                    html += `
                        <div class="card" style="margin: 1.5rem 0; border-left-color: ${value.color || 'var(--primary)'}">
                            ${value.icon ? `<div class="card-icon" style="background: ${value.color || 'var(--primary)'}"><i class="fas ${value.icon}"></i></div>` : ''}
                            <h3 style="color: var(--primary); margin-bottom: 0.75rem;">${value.title}</h3>
                            ${value.introduction ? `<p style="margin-bottom: 1rem;">${value.introduction}</p>` : ''}
                            ${value.steps.map(step => `
                                <div style="margin: 1rem 0; padding: 1rem; background: rgba(43, 43, 43, 0.4); border-radius: 4px;">
                                    <p style="font-weight: bold; color: var(--primary); margin-bottom: 0.5rem;">Step ${step.number}: ${step.title}</p>
                                    ${step.description ? `<p style="margin-bottom: 0.5rem;">${step.description}</p>` : ''}
                                    ${step.questions ? `
                                        <ul style="margin-top: 0.5rem; font-style: italic;">
                                            ${step.questions.map(q => `<li>${q}</li>`).join('')}
                                        </ul>
                                    ` : ''}
                                    ${step.quote ? `<p style="margin-top: 0.5rem; font-style: italic; color: var(--accent);">"${step.quote}"</p>` : ''}
                                </div>
                            `).join('')}
                        </div>
                    `;
                }
                // Regular objects with title and description
                else if (value.title && value.description) {
                    html += `
                        <div class="card" style="margin: 1.5rem 0;">
                            ${value.subtitle ? `<p style="color: var(--primary); font-weight: bold; margin-bottom: 0.5rem;">${value.subtitle}</p>` : ''}
                            <h3 style="color: var(--primary); margin-bottom: 0.75rem;">${value.title}</h3>
                            <p>${value.description}</p>
                            ${value.items ? `<ul style="margin-top: 0.75rem;">${value.items.map(item => `<li>${item}</li>`).join('')}</ul>` : ''}
                            ${value.distinction ? `<ul style="margin-top: 0.75rem;">${value.distinction.map(item => `<li>${item}</li>`).join('')}</ul>` : ''}
                            ${value.steps ? `<ol style="margin-top: 0.75rem;">${value.steps.map(step => `<li>${step}</li>`).join('')}</ol>` : ''}
                            ${value.keyInsight ? `<p style="margin-top: 1rem; padding: 0.75rem; background: rgba(196, 154, 108, 0.1); border-radius: 4px; font-style: italic;">${value.keyInsight}</p>` : ''}
                        </div>
                    `;
                } else if (value.question && value.reflection) {
                    html += `
                        <div class="card" style="margin: 1.5rem 0; background: rgba(196, 154, 108, 0.1);">
                            <p style="font-weight: bold; margin-bottom: 0.5rem;">${value.question}</p>
                            <p>${value.reflection}</p>
                        </div>
                    `;
                }
            } else if (Array.isArray(value)) {
                // Exercises, strategies, practical prompts
                if (key === 'exercises' || key === 'strategies' || key === 'practicalPrompts') {
                    html += `
                        <div style="margin: 1.5rem 0;">
                            <h4 style="color: var(--primary); margin-bottom: 1rem; text-transform: capitalize;">${key.replace(/([A-Z])/g, ' $1').trim()}</h4>
                            ${value.map(item => `
                                <div class="card" style="margin-bottom: 1rem;">
                                    ${item.number ? `<span style="color: var(--primary); font-weight: bold;">Step ${item.number}: </span>` : ''}
                                    ${item.title ? `<h4 style="color: var(--primary); margin-bottom: 0.5rem;">${item.title}</h4>` : ''}
                                    ${item.category ? `<p style="font-weight: bold; color: var(--primary); margin-bottom: 0.5rem;">${item.category}</p>` : ''}
                                    ${item.description ? `<p>${item.description}</p>` : ''}
                                    ${item.howTo ? `<p style="margin-top: 0.5rem;"><strong>How to:</strong> ${item.howTo}</p>` : ''}
                                    ${item.questions ? `
                                        <ul style="margin-top: 0.5rem;">
                                            ${item.questions.map(q => `<li>${q}</li>`).join('')}
                                        </ul>
                                    ` : ''}
                                </div>
                            `).join('')}
                        </div>
                    `;
                }
                // Ancient roots (slide 10)
                else if (key === 'ancientRoots') {
                    html += `
                        <div style="margin: 1.5rem 0;">
                            <h4 style="color: var(--primary); margin-bottom: 1rem;">Ancient Roots</h4>
                            ${value.map(root => `
                                <div class="card" style="margin-bottom: 1rem;">
                                    <p style="font-weight: bold; color: var(--primary); margin-bottom: 0.5rem;">${root.source}</p>
                                    <p style="font-style: italic; margin-bottom: 0.5rem;">"${root.quote}"</p>
                                    ${root.translation ? `<p>${root.translation}</p>` : ''}
                                    ${root.example ? `<p>${root.example}</p>` : ''}
                                </div>
                            `).join('')}
                        </div>
                    `;
                }
                // Parallels (slide 15)
                else if (key === 'parallels') {
                    html += `
                        <div class="grid-2" style="margin: 1.5rem 0;">
                            ${value.map(parallel => `
                                <div class="card">
                                    <p style="margin-bottom: 0.5rem;"><strong style="color: var(--primary);">Stoic:</strong> ${parallel.stoic}</p>
                                    <p><strong style="color: var(--secondary);">CBT:</strong> ${parallel.cbt}</p>
                                </div>
                            `).join('')}
                        </div>
                    `;
                }
                // Real world scenarios, core principles, benefits, etc.
                else if (key === 'realWorldScenarios' || key === 'corePrinciples' || key === 'mentalHealthBenefits') {
                    html += `
                        <div class="grid-2" style="margin: 1.5rem 0;">
                            ${value.map(item => `
                                <div class="card">
                                    ${item.icon ? `<div class="card-icon"><i class="fas ${item.icon}"></i></div>` : ''}
                                    ${item.scenario ? `<h4 style="color: var(--primary);">${item.scenario}</h4>` : ''}
                                    ${item.benefit ? `<h4 style="color: var(--primary);">${item.benefit}</h4>` : ''}
                                    ${item.title ? `<h4 style="color: var(--primary);">${item.title}</h4>` : ''}
                                    ${item.situation ? `<p style="margin-bottom: 0.5rem;"><strong>Situation:</strong> ${item.situation}</p>` : ''}
                                    ${item.stoicResponse ? `<p><strong style="color: var(--primary);">Stoic Response:</strong> ${item.stoicResponse}</p>` : ''}
                                    ${item.description ? `<p>${item.description}</p>` : ''}
                                </div>
                            `).join('')}
                        </div>
                    `;
                }
            } else if (typeof value === 'string' && (key === 'paradox' || key === 'clarification' || key === 'powerOfHabit' || key === 'senecaPractice' || key === 'reminder' || key === 'sabsAsTool')) {
                html += `
                    <div class="card" style="margin: 1.5rem 0; background: rgba(196, 154, 108, 0.1);">
                        <p style="font-style: italic;">${value}</p>
                    </div>
                `;
            }
        });

        return html;
    }

    setupEventListeners() {
        // Navigation buttons
        document.getElementById('prev-btn').addEventListener('click', () => this.prevSlide());
        document.getElementById('next-btn').addEventListener('click', () => this.nextSlide());

        // Keyboard navigation
        document.addEventListener('keydown', (e) => {
            switch(e.key) {
                case 'ArrowLeft':
                case 'PageUp':
                    this.prevSlide();
                    break;
                case 'ArrowRight':
                case 'PageDown':
                case ' ':
                    e.preventDefault();
                    this.nextSlide();
                    break;
                case 'Home':
                    this.goToSlide(0);
                    break;
                case 'End':
                    this.goToSlide(this.slides.length - 1);
                    break;
                case 'Escape':
                    this.toggleOverview();
                    break;
                case 'f':
                case 'F':
                    this.toggleFullscreen();
                    break;
                case 'a':
                case 'A':
                    this.toggleAutoPlay();
                    break;
            }
        });

        // Touch/Swipe support
        const container = document.getElementById('slide-container');
        container.addEventListener('touchstart', (e) => {
            this.touchStartX = e.changedTouches[0].screenX;
        });

        container.addEventListener('touchend', (e) => {
            this.touchEndX = e.changedTouches[0].screenX;
            this.handleSwipe();
        });

        // Overview mode
        document.getElementById('overview-btn').addEventListener('click', () => this.toggleOverview());
        document.getElementById('overview-close').addEventListener('click', () => this.toggleOverview());

        // Fullscreen
        document.getElementById('fullscreen-btn').addEventListener('click', () => this.toggleFullscreen());

        // Auto-play
        document.getElementById('autoplay-btn').addEventListener('click', () => this.toggleAutoPlay());
    }

    handleSwipe() {
        const swipeThreshold = 50;
        const diff = this.touchStartX - this.touchEndX;

        if (Math.abs(diff) > swipeThreshold) {
            if (diff > 0) {
                this.nextSlide();
            } else {
                this.prevSlide();
            }
        }
    }

    nextSlide() {
        if (this.currentSlide < this.slides.length - 1) {
            this.goToSlide(this.currentSlide + 1);
        }
    }

    prevSlide() {
        if (this.currentSlide > 0) {
            this.goToSlide(this.currentSlide - 1);
        }
    }

    goToSlide(index) {
        if (index < 0 || index >= this.slides.length) return;

        const slideElements = document.querySelectorAll('.slide');

        // Remove active class from current
        slideElements[this.currentSlide].classList.remove('active');
        slideElements[this.currentSlide].classList.add('prev');

        // Add active class to new
        this.currentSlide = index;
        slideElements[this.currentSlide].classList.remove('prev');
        slideElements[this.currentSlide].classList.add('active');

        this.updateUI();
    }

    updateUI() {
        // Update slide counter
        document.getElementById('current-slide').textContent = this.currentSlide + 1;

        // Update progress bar
        const progress = ((this.currentSlide + 1) / this.slides.length) * 100;
        document.getElementById('progress-fill').style.width = `${progress}%`;

        // Update navigation buttons
        const prevBtn = document.getElementById('prev-btn');
        const nextBtn = document.getElementById('next-btn');

        prevBtn.disabled = this.currentSlide === 0;
        nextBtn.disabled = this.currentSlide === this.slides.length - 1;
    }

    setupOverview() {
        const grid = document.getElementById('overview-grid');
        grid.innerHTML = this.slides.map((slide, index) => `
            <div class="overview-slide ${index === this.currentSlide ? 'current' : ''}" data-index="${index}">
                <div class="overview-number">Slide ${index + 1}</div>
                <div class="overview-title">${slide.title || slide.subtitle || 'Chapter ' + slide.chapterNumber}</div>
                <div style="color: var(--accent); font-size: 0.85rem; margin-top: 0.25rem;">${slide.type}</div>
            </div>
        `).join('');

        // Add click handlers
        grid.querySelectorAll('.overview-slide').forEach(el => {
            el.addEventListener('click', () => {
                const index = parseInt(el.dataset.index);
                this.goToSlide(index);
                this.toggleOverview();
            });
        });
    }

    toggleOverview() {
        const overview = document.getElementById('overview-mode');
        overview.classList.toggle('active');

        // Update current slide highlight
        if (overview.classList.contains('active')) {
            const overviewSlides = document.querySelectorAll('.overview-slide');
            overviewSlides.forEach((el, index) => {
                el.classList.toggle('current', index === this.currentSlide);
            });
        }
    }

    toggleFullscreen() {
        if (!document.fullscreenElement) {
            document.documentElement.requestFullscreen();
            document.getElementById('app').classList.add('fullscreen-active');
            document.getElementById('fullscreen-btn').innerHTML = '<i class="fas fa-compress"></i><span>Exit Fullscreen</span>';
        } else {
            document.exitFullscreen();
            document.getElementById('app').classList.remove('fullscreen-active');
            document.getElementById('fullscreen-btn').innerHTML = '<i class="fas fa-expand"></i><span>Fullscreen</span>';
        }
    }

    toggleAutoPlay() {
        if (this.autoPlayInterval) {
            // Stop auto-play
            clearInterval(this.autoPlayInterval);
            this.autoPlayInterval = null;
            document.getElementById('autoplay-btn').innerHTML = '<i class="fas fa-play"></i><span>Auto-play</span>';
        } else {
            // Start auto-play
            this.autoPlayInterval = setInterval(() => {
                if (this.currentSlide < this.slides.length - 1) {
                    this.nextSlide();
                } else {
                    // Stop when reaching the end
                    this.toggleAutoPlay();
                }
            }, this.autoPlayDelay);
            document.getElementById('autoplay-btn').innerHTML = '<i class="fas fa-pause"></i><span>Pause</span>';
        }
    }
}

// Initialize app when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    new PresentationApp();
});
