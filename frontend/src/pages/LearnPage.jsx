import React, { useState, useEffect } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { api } from '../services/api';
import confetti from 'canvas-confetti';
import { 
  BookOpen, 
  CheckCircle, 
  Clock, 
  Award, 
  AlertTriangle, 
  ArrowRight, 
  ArrowLeft, 
  Sparkles, 
  IndianRupee, 
  ExternalLink,
  RotateCcw,
  HelpCircle,
  ShieldCheck
} from 'lucide-react';
import { HighlightedText } from '../components/HighlightedText';
import { FormattedExplanation } from '../components/FormattedExplanation';

export const LearnPage = () => {
  const { moduleSlug } = useParams();
  const navigate = useNavigate();

  const [modules, setModules] = useState([]);
  const [activeModule, setActiveModule] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Quiz state
  const [selectedAnswers, setSelectedAnswers] = useState({});
  const [quizResult, setQuizResult] = useState(null);
  const [submittingQuiz, setSubmittingQuiz] = useState(false);

  // Load modules list
  useEffect(() => {
    const fetchModules = async () => {
      try {
        setLoading(true);
        const data = await api.getModules();
        setModules(data);
      } catch (err) {
        setError(err.message || 'Failed to load educational modules');
      } finally {
        setLoading(false);
      }
    };
    fetchModules();
  }, []);

  // Load single module detail if slug is present in URL
  useEffect(() => {
    if (!moduleSlug) {
      setActiveModule(null);
      setQuizResult(null);
      setSelectedAnswers({});
      return;
    }

    const fetchDetail = async () => {
      try {
        setLoading(true);
        const detail = await api.getModuleDetail(moduleSlug);
        setActiveModule(detail);
        setQuizResult(null);
        setSelectedAnswers({});
        window.scrollTo(0, 0);
      } catch (err) {
        setError(err.message || 'Failed to load module detail');
      } finally {
        setLoading(false);
      }
    };
    fetchDetail();
  }, [moduleSlug]);

  const handleAnswerSelect = (questionId, optionIndex) => {
    if (quizResult) return; // Prevent changing after submission
    setSelectedAnswers(prev => ({
      ...prev,
      [questionId]: optionIndex
    }));
  };

  const handleSubmitQuiz = async () => {
    if (!activeModule || !activeModule.quizzes) return;
    
    // Check all answered
    const unanswered = activeModule.quizzes.some(q => selectedAnswers[q.id] === undefined);
    if (unanswered) {
      alert('Please select an answer for all questions before submitting.');
      return;
    }

    setSubmittingQuiz(true);
    try {
      const result = await api.submitQuiz(selectedAnswers);
      setQuizResult(result);

      if (result.passed) {
        confetti({
          particleCount: 80,
          spread: 70,
          origin: { y: 0.6 }
        });
        // Update module in local list
        setModules(prev => prev.map(m => m.slug === activeModule.slug ? { ...m, is_completed: true } : m));
      }
    } catch (err) {
      alert(err.message || 'Failed to submit quiz');
    } finally {
      setSubmittingQuiz(false);
    }
  };

  const handleResetQuiz = () => {
    setSelectedAnswers({});
    setQuizResult(null);
  };

  const completedCount = modules.filter(m => m.is_completed).length;
  const progressPercent = modules.length > 0 ? Math.round((completedCount / modules.length) * 100) : 0;

  if (loading && !activeModule && modules.length === 0) {
    return (
      <div className="max-w-4xl mx-auto py-20 px-4 text-center">
        <div className="w-10 h-10 border-3 border-teal-700 border-t-transparent rounded-full animate-spin mx-auto mb-4" />
        <p className="text-sm text-slate-500">Loading educational curriculum...</p>
      </div>
    );
  }

  // --- DETAIL VIEW: Single Module Learning Experience ---
  if (activeModule) {
    const currentIndex = modules.findIndex(m => m.slug === activeModule.slug);
    const prevModule = currentIndex > 0 ? modules[currentIndex - 1] : null;
    const nextModule = currentIndex < modules.length - 1 ? modules[currentIndex + 1] : null;

    return (
      <div className="max-w-4xl mx-auto px-4 sm:px-6 py-8 space-y-8">
        {/* Navigation & Breadcrumbs */}
        <div className="flex items-center justify-between pb-4 border-b border-slate-200">
          <button
            onClick={() => navigate('/learn')}
            className="flex items-center gap-1.5 text-xs font-semibold text-slate-600 hover:text-teal-800 transition-colors cursor-pointer"
          >
            <ArrowLeft className="w-4 h-4" />
            <span>Back to All 10 Modules</span>
          </button>

          <div className="flex items-center gap-2">
            <span className="text-xs text-slate-400">Module {currentIndex + 1} of {modules.length}</span>
            {activeModule.is_completed && (
              <span className="flex items-center gap-1 text-[11px] font-semibold text-emerald-800 bg-emerald-50 px-2 py-0.5 rounded-full border border-emerald-200">
                <CheckCircle className="w-3.5 h-3.5" /> Completed
              </span>
            )}
          </div>
        </div>

        {/* Module Header */}
        <div className="space-y-3">
          <div className="flex items-center gap-2">
            <span className="text-[11px] font-bold px-2.5 py-0.5 rounded-full bg-teal-50 text-teal-800 border border-teal-200 uppercase tracking-wider">
              {activeModule.category}
            </span>
            <span className="flex items-center gap-1 text-xs text-slate-500">
              <Clock className="w-3.5 h-3.5 text-slate-400" />
              {activeModule.estimated_minutes} min read
            </span>
            <span className="text-xs px-2 py-0.5 rounded bg-slate-100 text-slate-600 font-medium">
              {activeModule.level}
            </span>
          </div>

          <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-900 tracking-tight">
            {activeModule.title}
          </h1>
          {activeModule.subtitle && (
            <p className="text-sm text-slate-600 leading-relaxed">
              {activeModule.subtitle}
            </p>
          )}
        </div>

        {/* 1. Core Concept Explanation */}
        <section className="bg-white rounded-2xl p-6 sm:p-8 border border-slate-200 shadow-xs space-y-4">
          <div className="flex items-center gap-2 text-teal-900 font-bold text-xs uppercase tracking-wider">
            <BookOpen className="w-4 h-4 text-teal-700" />
            Core Concept Explanation
          </div>
          <FormattedExplanation content={activeModule.concept_explanation} textColor="text-slate-700" />
        </section>

        {/* 2. Why It Matters */}
        <section className="bg-white rounded-2xl p-6 sm:p-8 border border-slate-200 shadow-xs space-y-3">
          <div className="flex items-center gap-2 text-indigo-900 font-bold text-xs uppercase tracking-wider">
            <ShieldCheck className="w-4 h-4 text-indigo-700" />
            Why This Concept Matters Before You Buy
          </div>
          <FormattedExplanation content={activeModule.why_it_matters} textColor="text-slate-700" />
        </section>

        {/* 3. Practical Indian Rupee Example */}
        <section className="bg-amber-50/70 rounded-2xl p-6 sm:p-8 border border-amber-200/80 shadow-xs space-y-3">
          <div className="flex items-center gap-2 text-amber-900 font-bold text-xs uppercase tracking-wider">
            <IndianRupee className="w-4 h-4 text-amber-700" />
            Everyday Practical Indian Example
          </div>
          <FormattedExplanation content={activeModule.practical_indian_example} textColor="text-amber-950/90" />
        </section>

        {/* 4. Common Mistakes & Misconceptions */}
        {activeModule.common_mistakes && activeModule.common_mistakes.length > 0 && (
          <section className="bg-rose-50/50 rounded-2xl p-6 sm:p-8 border border-rose-200/70 shadow-xs space-y-3">
            <div className="flex items-center gap-2 text-rose-900 font-bold text-xs uppercase tracking-wider">
              <AlertTriangle className="w-4 h-4 text-rose-700" />
              Common Mistakes & Misconceptions to Avoid
            </div>
            <ul className="space-y-2">
              {activeModule.common_mistakes.map((mistake, idx) => (
                <li key={idx} className="flex items-start gap-2.5 text-xs text-rose-950/90 leading-relaxed">
                  <span className="w-1.5 h-1.5 rounded-full bg-rose-600 mt-1.5 shrink-0" />
                  <span><HighlightedText text={mistake} /></span>
                </li>
              ))}
            </ul>
          </section>
        )}

        {/* 5. Key Takeaways */}
        {activeModule.key_takeaways && activeModule.key_takeaways.length > 0 && (
          <section className="bg-emerald-50/50 rounded-2xl p-6 sm:p-8 border border-emerald-200/70 shadow-xs space-y-3">
            <div className="flex items-center gap-2 text-emerald-900 font-bold text-xs uppercase tracking-wider">
              <CheckCircle className="w-4 h-4 text-emerald-700" />
              Golden Rules & Key Takeaways
            </div>
            <ul className="space-y-2">
              {activeModule.key_takeaways.map((takeaway, idx) => (
                <li key={idx} className="flex items-start gap-2.5 text-xs text-emerald-950/90 leading-relaxed">
                  <span className="w-1.5 h-1.5 rounded-full bg-emerald-600 mt-1.5 shrink-0" />
                  <span><HighlightedText text={takeaway} /></span>
                </li>
              ))}
            </ul>
          </section>
        )}

        {/* 6. Knowledge Check Quiz */}
        {activeModule.quizzes && activeModule.quizzes.length > 0 && (
          <section className="bg-white rounded-2xl p-6 sm:p-8 border border-slate-200 shadow-sm space-y-6">
            <div className="flex items-center justify-between pb-3 border-b border-slate-100">
              <div className="flex items-center gap-2">
                <HelpCircle className="w-5 h-5 text-teal-700" />
                <h3 className="text-base font-bold text-slate-900">Knowledge Check Quiz</h3>
              </div>
              <span className="text-xs text-slate-500 font-medium">
                {activeModule.quizzes.length} Question{activeModule.quizzes.length > 1 ? 's' : ''}
              </span>
            </div>

            <div className="space-y-6">
              {activeModule.quizzes.map((q, qIdx) => {
                const chosen = selectedAnswers[q.id];
                const evaluated = quizResult?.results?.find(r => r.question_id === q.id);

                return (
                  <div key={q.id} className="space-y-3">
                    <p className="text-sm font-semibold text-slate-850 text-slate-900">
                      {qIdx + 1}. {q.question}
                    </p>

                    <div className="space-y-2">
                      {q.options.map((opt, oIdx) => {
                        let btnStyle = 'border-slate-200 hover:bg-slate-50 text-slate-700';
                        if (chosen === oIdx) {
                          btnStyle = 'border-teal-700 bg-teal-50 text-teal-900 font-semibold ring-1 ring-teal-700';
                        }
                        if (evaluated) {
                          if (oIdx === evaluated.correct_option_index) {
                            btnStyle = 'border-emerald-500 bg-emerald-50 text-emerald-900 font-semibold ring-1 ring-emerald-500';
                          } else if (chosen === oIdx && !evaluated.is_correct) {
                            btnStyle = 'border-rose-500 bg-rose-50 text-rose-900 line-through';
                          } else {
                            btnStyle = 'border-slate-200 opacity-60 text-slate-500';
                          }
                        }

                        return (
                          <button
                            key={oIdx}
                            disabled={!!quizResult}
                            onClick={() => handleAnswerSelect(q.id, oIdx)}
                            className={`w-full text-left p-3.5 rounded-xl border text-xs transition-all flex items-start gap-2.5 cursor-pointer ${btnStyle}`}
                          >
                            <span className="w-5 h-5 rounded-full border border-current flex items-center justify-center shrink-0 text-[10px] font-bold">
                              {String.fromCharCode(65 + oIdx)}
                            </span>
                            <span className="leading-relaxed">{opt}</span>
                          </button>
                        );
                      })}
                    </div>

                    {/* Feedback explanation */}
                    {evaluated && (
                      <div className={`p-3.5 rounded-xl text-xs leading-relaxed border ${
                        evaluated.is_correct 
                          ? 'bg-emerald-50/80 border-emerald-200 text-emerald-950' 
                          : 'bg-rose-50/80 border-rose-200 text-rose-950'
                      }`}>
                        <div className="font-bold mb-1 flex items-center gap-1.5">
                          {evaluated.is_correct ? '✅ Correct!' : '❌ Incorrect choice.'}
                        </div>
                        <p>{evaluated.explanation}</p>
                      </div>
                    )}
                  </div>
                );
              })}
            </div>

            {/* Quiz Action Buttons */}
            <div className="pt-2 flex items-center justify-between">
              {!quizResult ? (
                <button
                  disabled={submittingQuiz}
                  onClick={handleSubmitQuiz}
                  className="px-6 py-2.5 rounded-xl bg-teal-800 hover:bg-teal-900 text-white font-semibold text-xs transition-all shadow-xs disabled:opacity-50 cursor-pointer"
                >
                  {submittingQuiz ? 'Evaluating...' : 'Check My Answers'}
                </button>
              ) : (
                <div className="flex items-center gap-3 w-full justify-between">
                  <div className="text-xs">
                    <span className="font-bold text-slate-800">
                      Score: {quizResult.score} / {quizResult.total} ({quizResult.percentage}%)
                    </span>
                    <span className={`ml-2 font-medium ${quizResult.passed ? 'text-emerald-700' : 'text-amber-700'}`}>
                      {quizResult.passed ? '🎉 Passed! Module Completed.' : 'Review explanations and try again.'}
                    </span>
                  </div>
                  <button
                    onClick={handleResetQuiz}
                    className="flex items-center gap-1 text-xs font-semibold text-teal-800 hover:text-teal-900 border border-teal-200 px-3 py-1.5 rounded-lg cursor-pointer"
                  >
                    <RotateCcw className="w-3.5 h-3.5" /> Retake Quiz
                  </button>
                </div>
              )}
            </div>
          </section>
        )}

        {/* 7. Official Source Links */}
        {activeModule.official_source_links && activeModule.official_source_links.length > 0 && (
          <div className="p-4 bg-slate-50 rounded-xl border border-slate-200 text-xs flex flex-wrap items-center gap-4 text-slate-600">
            <span className="font-semibold text-slate-700">Official Indian Sources:</span>
            {activeModule.official_source_links.map((src, i) => (
              <a
                key={i}
                href={src.url}
                target="_blank"
                rel="noopener noreferrer"
                className="text-teal-700 hover:underline flex items-center gap-1"
              >
                {src.title} <ExternalLink className="w-3 h-3" />
              </a>
            ))}
          </div>
        )}

        {/* Previous / Next Module Navigation */}
        <div className="pt-6 border-t border-slate-200 flex items-center justify-between">
          {prevModule ? (
            <button
              onClick={() => navigate(`/learn/${prevModule.slug}`)}
              className="px-4 py-2 rounded-xl border border-slate-300 text-slate-700 hover:bg-slate-100 text-xs font-medium flex items-center gap-1.5 transition-colors cursor-pointer"
            >
              <ArrowLeft className="w-3.5 h-3.5" />
              <span>Prev: {prevModule.title.substring(0, 24)}...</span>
            </button>
          ) : <div />}

          {nextModule ? (
            <button
              onClick={() => navigate(`/learn/${nextModule.slug}`)}
              className="px-5 py-2 rounded-xl bg-teal-800 hover:bg-teal-900 text-white text-xs font-semibold flex items-center gap-1.5 transition-colors shadow-xs cursor-pointer"
            >
              <span>Next: {nextModule.title.substring(0, 24)}...</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </button>
          ) : (
            <button
              onClick={() => navigate('/explore')}
              className="px-5 py-2 rounded-xl bg-teal-800 hover:bg-teal-900 text-white text-xs font-semibold flex items-center gap-1.5 transition-colors shadow-xs cursor-pointer"
            >
              <span>Explore Policies Now</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </button>
          )}
        </div>
      </div>
    );
  }

  // --- ROADMAP VIEW: All 10 Modules Overview ---
  return (
    <div className="max-w-5xl mx-auto px-4 sm:px-6 py-10 space-y-10">
      {/* Top Banner */}
      <div className="text-center max-w-2xl mx-auto space-y-3">
        <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-teal-50 text-teal-800 text-xs font-semibold border border-teal-200">
          <BookOpen className="w-3.5 h-3.5" />
          <span>Option A: Zero-Cost Insurance University</span>
        </div>
        <h1 className="text-3xl font-extrabold text-slate-900 tracking-tight">
          Learn Insurance From the Ground Up
        </h1>
        <p className="text-sm text-slate-600 leading-relaxed font-normal">
          Designed for complete beginners. 10 bite-sized modules explaining core concepts with practical Indian numbers, real claims examples, and quick knowledge checks.
        </p>

        {/* Progress Tracker Card */}
        <div className="mt-6 p-5 bg-white rounded-2xl border border-slate-200 shadow-xs max-w-lg mx-auto">
          <div className="flex items-center justify-between text-xs font-semibold mb-2">
            <span className="text-slate-700">Curriculum Progress</span>
            <span className="text-teal-800 font-bold">{completedCount} of {modules.length} Completed ({progressPercent}%)</span>
          </div>
          <div className="w-full h-2.5 bg-slate-100 rounded-full overflow-hidden">
            <div 
              className="h-full bg-teal-700 rounded-full transition-all duration-500 ease-out"
              style={{ width: `${progressPercent}%` }}
            />
          </div>
        </div>
      </div>

      {/* Modules Roadmap Grid */}
      <div className="space-y-4">
        {modules.map((m, index) => {
          return (
            <div
              key={m.slug}
              onClick={() => navigate(`/learn/${m.slug}`)}
              className="bg-white rounded-2xl p-5 sm:p-6 border border-slate-200/90 shadow-xs hover:border-teal-600 hover:shadow-md transition-all cursor-pointer flex flex-col sm:flex-row sm:items-center justify-between gap-4 group"
            >
              <div className="flex items-start gap-4">
                <div className={`w-10 h-10 rounded-xl flex items-center justify-center font-bold text-sm shrink-0 transition-colors ${
                  m.is_completed 
                    ? 'bg-emerald-100 text-emerald-800' 
                    : 'bg-teal-50 text-teal-800 group-hover:bg-teal-800 group-hover:text-white'
                }`}>
                  {m.is_completed ? <CheckCircle className="w-5 h-5 text-emerald-700" /> : index + 1}
                </div>

                <div className="space-y-1">
                  <div className="flex items-center gap-2">
                    <span className="text-[10px] font-bold uppercase tracking-wider px-2 py-0.2 rounded-sm bg-slate-100 text-slate-700">
                      {m.category}
                    </span>
                    <span className="flex items-center gap-1 text-[11px] text-slate-400">
                      <Clock className="w-3 h-3" /> {m.estimated_minutes} min read
                    </span>
                    <span className="text-[10px] px-1.5 py-0.2 rounded bg-slate-50 text-slate-500 border border-slate-200">
                      {m.level}
                    </span>
                  </div>

                  <h3 className="text-base font-bold text-slate-900 group-hover:text-teal-800 transition-colors">
                    {m.title}
                  </h3>
                  {m.subtitle && (
                    <p className="text-xs text-slate-500 line-clamp-1">
                      {m.subtitle}
                    </p>
                  )}
                </div>
              </div>

              <div className="flex items-center gap-3 shrink-0 self-end sm:self-center">
                {m.is_completed ? (
                  <span className="text-xs font-semibold text-emerald-700 flex items-center gap-1">
                    <CheckCircle className="w-4 h-4" /> Completed
                  </span>
                ) : (
                  <span className="text-xs font-semibold text-teal-800 flex items-center gap-1 group-hover:translate-x-1 transition-transform">
                    Start Module <ArrowRight className="w-4 h-4" />
                  </span>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
