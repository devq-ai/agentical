"""
Advanced Capability Matching Algorithms for Agentical Playbook System

This module provides sophisticated algorithms for matching agent capabilities
to playbook requirements, including fuzzy matching, preference learning,
load balancing optimization, and multi-criteria decision analysis.

Features:
- Advanced scoring algorithms with configurable weights
- Fuzzy matching for capability names and descriptions
- Machine learning-based preference optimization
- Load balancing and resource optimization
- Multi-objective optimization for complex scenarios
- Performance prediction and estimation
- Dynamic algorithm selection based on context
"""

import asyncio
import logging
import math
import statistics
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Set, Union, Tuple, Callable
from collections import defaultdict
from dataclasses import dataclass
from enum import Enum

try:
    import logfire
except ImportError:
    class MockLogfire:
        @staticmethod
        def span(name, **kwargs):
            class MockSpan:
                def __enter__(self): return self
                def __exit__(self, *args): pass
            return MockSpan()
        @staticmethod
        def info(*args, **kwargs): pass
        @staticmethod
        def error(*args, **kwargs): pass
    logfire = MockLogfire()

from .playbook_capabilities import (
    AgentPoolEntry, PlaybookCapability, CapabilityFilter, CapabilityMatchResult,
    HealthStatus, PerformanceMetrics, CapabilityComplexity
)

logger = logging.getLogger(__name__)


class MatchingAlgorithm(str, Enum):
    """Available matching algorithms."""
    WEIGHTED_SCORE = "weighted_score"
    FUZZY_MATCH = "fuzzy_match"
    PERFORMANCE_OPTIMIZED = "performance_optimized"
    LOAD_BALANCED = "load_balanced"
    COST_OPTIMIZED = "cost_optimized"
    MULTI_OBJECTIVE = "multi_objective"
    MACHINE_LEARNING = "machine_learning"


class OptimizationObjective(str, Enum):
    """Optimization objectives for multi-criteria matching."""
    MINIMIZE_TIME = "minimize_time"
    MAXIMIZE_RELIABILITY = "maximize_reliability"
    MINIMIZE_COST = "minimize_cost"
    BALANCE_LOAD = "balance_load"
    MAXIMIZE_PERFORMANCE = "maximize_performance"
    MINIMIZE_COMPLEXITY = "minimize_complexity"


@dataclass
class MatchingWeights:
    """Configurable weights for different matching criteria."""
    capability_match: float = 0.30
    tool_availability: float = 0.25
    workflow_support: float = 0.15
    performance_history: float = 0.15
    availability: float = 0.10
    cost_efficiency: float = 0.05

    def normalize(self) -> 'MatchingWeights':
        """Normalize weights to sum to 1.0."""
        total = sum([
            self.capability_match, self.tool_availability, self.workflow_support,
            self.performance_history, self.availability, self.cost_efficiency
        ])

        if total == 0:
            return MatchingWeights()

        return MatchingWeights(
            capability_match=self.capability_match / total,
            tool_availability=self.tool_availability / total,
            workflow_support=self.workflow_support / total,
            performance_history=self.performance_history / total,
            availability=self.availability / total,
            cost_efficiency=self.cost_efficiency / total
        )


@dataclass
class MatchingContext:
    """Context information for capability matching."""
    playbook_id: Optional[str] = None
    step_count: int = 1
    estimated_duration: float = 300.0  # seconds
    priority: int = 5  # 1-10 scale
    deadline: Optional[datetime] = None
    budget_limit: Optional[float] = None
    prefer_reliable: bool = True
    allow_parallel: bool = True
    environment: str = "production"
    user_preferences: Dict[str, Any] = None

    def __post_init__(self):
        if self.user_preferences is None:
            self.user_preferences = {}


class AdvancedCapabilityMatcher:
    """Advanced capability matching engine with multiple algorithms."""

    def __init__(self):
        """Initialize the capability matcher."""
        self.matching_history: List[Dict[str, Any]] = []
        self.agent_performance_cache: Dict[str, Dict[str, float]] = {}
        self.preference_weights: Dict[str, MatchingWeights] = {}
        self.fuzzy_threshold = 0.7
        self.learning_rate = 0.1

    async def find_best_matches(
        self,
        agents: List[AgentPoolEntry],
        requirements: CapabilityFilter,
        context: MatchingContext,
        algorithm: MatchingAlgorithm = MatchingAlgorithm.WEIGHTED_SCORE,
        max_results: int = 10
    ) -> List[CapabilityMatchResult]:
        """
        Find best agent matches using the specified algorithm.

        Args:
            agents: Available agents to consider
            requirements: Capability requirements
            context: Matching context
            algorithm: Matching algorithm to use
            max_results: Maximum number of results

        Returns:
            List of capability match results
        """
        with logfire.span("Advanced capability matching", algorithm=algorithm.value):
            try:
                # Select and apply matching algorithm
                if algorithm == MatchingAlgorithm.WEIGHTED_SCORE:
                    matches = await self._weighted_score_matching(agents, requirements, context)
                elif algorithm == MatchingAlgorithm.FUZZY_MATCH:
                    matches = await self._fuzzy_matching(agents, requirements, context)
                elif algorithm == MatchingAlgorithm.PERFORMANCE_OPTIMIZED:
                    matches = await self._performance_optimized_matching(agents, requirements, context)
                elif algorithm == MatchingAlgorithm.LOAD_BALANCED:
                    matches = await self._load_balanced_matching(agents, requirements, context)
                elif algorithm == MatchingAlgorithm.COST_OPTIMIZED:
                    matches = await self._cost_optimized_matching(agents, requirements, context)
                elif algorithm == MatchingAlgorithm.MULTI_OBJECTIVE:
                    matches = await self._multi_objective_matching(agents, requirements, context)
                elif algorithm == MatchingAlgorithm.MACHINE_LEARNING:
                    matches = await self._ml_based_matching(agents, requirements, context)
                else:
                    matches = await self._weighted_score_matching(agents, requirements, context)

                # Sort and limit results
                matches.sort(key=lambda x: x.match_score, reverse=True)
                results = matches[:max_results]

                # Record matching for learning
                await self._record_matching_result(requirements, context, results, algorithm)

                logfire.info("Capability matching completed",
                           algorithm=algorithm.value,
                           candidates=len(agents),
                           matches=len(results))

                return results

            except Exception as e:
                logfire.error("Capability matching failed", error=str(e))
                logger.error(f"Capability matching failed: {e}")
                return []

    async def _weighted_score_matching(
        self,
        agents: List[AgentPoolEntry],
        requirements: CapabilityFilter,
        context: MatchingContext
    ) -> List[CapabilityMatchResult]:
        """Standard weighted score matching algorithm."""

        weights = self._get_contextual_weights(context)
        matches = []

        for agent in agents:
            if not self._passes_basic_requirements(agent, requirements):
                continue

            # Calculate individual scores
            capability_score = self._calculate_capability_score(agent, requirements)
            tool_score = self._calculate_tool_score(agent, requirements)
            workflow_score = self._calculate_workflow_score(agent, requirements)
            performance_score = self._calculate_performance_score(agent, context)
            availability_score = self._calculate_availability_score(agent)
            cost_score = self._calculate_cost_score(agent, context)

            # Calculate weighted total
            total_score = (
                weights.capability_match * capability_score +
                weights.tool_availability * tool_score +
                weights.workflow_support * workflow_score +
                weights.performance_history * performance_score +
                weights.availability * availability_score +
                weights.cost_efficiency * cost_score
            )

            # Create match result
            match = CapabilityMatchResult(
                agent_id=agent.agent_id,
                match_score=min(total_score, 1.0),
                capability_score=capability_score,
                tool_score=tool_score,
                workflow_score=workflow_score,
                performance_score=performance_score,
                availability_score=availability_score,
                estimated_execution_time=self._estimate_execution_time(agent, context),
                estimated_cost=self._estimate_cost(agent, context),
                confidence_level=self._calculate_confidence(agent, requirements)
            )

            matches.append(match)

        return matches

    async def _fuzzy_matching(
        self,
        agents: List[AgentPoolEntry],
        requirements: CapabilityFilter,
        context: MatchingContext
    ) -> List[CapabilityMatchResult]:
        """Fuzzy matching algorithm for flexible capability matching."""

        matches = []

        for agent in agents:
            fuzzy_scores = []

            # Fuzzy capability matching
            for req_step_type in requirements.step_types:
                best_fuzzy_score = 0.0
                for capability in agent.capabilities:
                    for supported_step in capability.supported_step_types:
                        fuzzy_score = self._calculate_fuzzy_similarity(req_step_type, supported_step)
                        best_fuzzy_score = max(best_fuzzy_score, fuzzy_score)
                fuzzy_scores.append(best_fuzzy_score)

            # Fuzzy tool matching
            tool_fuzzy_scores = []
            for req_tool in requirements.required_tools:
                best_tool_score = 0.0
                for available_tool in agent.available_tools:
                    tool_fuzzy_score = self._calculate_fuzzy_similarity(req_tool, available_tool)
                    best_tool_score = max(best_tool_score, tool_fuzzy_score)
                tool_fuzzy_scores.append(best_tool_score)

            # Calculate overall fuzzy score
            capability_fuzzy = statistics.mean(fuzzy_scores) if fuzzy_scores else 0.0
            tool_fuzzy = statistics.mean(tool_fuzzy_scores) if tool_fuzzy_scores else 1.0

            # Combine with other factors
            availability_score = self._calculate_availability_score(agent)
            performance_score = self._calculate_performance_score(agent, context)

            total_fuzzy_score = (
                0.4 * capability_fuzzy +
                0.3 * tool_fuzzy +
                0.2 * availability_score +
                0.1 * performance_score
            )

            if total_fuzzy_score >= self.fuzzy_threshold:
                match = CapabilityMatchResult(
                    agent_id=agent.agent_id,
                    match_score=total_fuzzy_score,
                    capability_score=capability_fuzzy,
                    tool_score=tool_fuzzy,
                    availability_score=availability_score,
                    performance_score=performance_score,
                    confidence_level=total_fuzzy_score * 0.8,  # Lower confidence for fuzzy
                    estimated_execution_time=self._estimate_execution_time(agent, context),
                    estimated_cost=self._estimate_cost(agent, context)
                )
                matches.append(match)

        return matches

    async def _performance_optimized_matching(
        self,
        agents: List[AgentPoolEntry],
        requirements: CapabilityFilter,
        context: MatchingContext
    ) -> List[CapabilityMatchResult]:
        """Performance-optimized matching focusing on execution speed and reliability."""

        matches = []

        for agent in agents:
            if not self._passes_basic_requirements(agent, requirements):
                continue

            # Heavy weight on performance metrics
            performance_score = self._calculate_performance_score(agent, context)
            reliability_score = self._calculate_reliability_score(agent)
            speed_score = self._calculate_speed_score(agent, context)

            # Basic capability checking
            capability_score = self._calculate_capability_score(agent, requirements)
            tool_score = self._calculate_tool_score(agent, requirements)

            # Performance-optimized weights
            total_score = (
                0.25 * capability_score +
                0.20 * tool_score +
                0.30 * performance_score +
                0.15 * reliability_score +
                0.10 * speed_score
            )

            match = CapabilityMatchResult(
                agent_id=agent.agent_id,
                match_score=total_score,
                capability_score=capability_score,
                tool_score=tool_score,
                performance_score=performance_score,
                estimated_execution_time=self._estimate_execution_time(agent, context),
                estimated_cost=self._estimate_cost(agent, context),
                confidence_level=reliability_score
            )

            matches.append(match)

        return matches

    async def _load_balanced_matching(
        self,
        agents: List[AgentPoolEntry],
        requirements: CapabilityFilter,
        context: MatchingContext
    ) -> List[CapabilityMatchResult]:
        """Load-balanced matching to distribute work evenly across agents."""

        matches = []

        # Calculate load distribution statistics
        total_capacity = sum(agent.max_concurrent_executions for agent in agents)
        total_load = sum(agent.current_load for agent in agents)
        avg_load_percentage = (total_load / total_capacity * 100) if total_capacity > 0 else 0

        for agent in agents:
            if not self._passes_basic_requirements(agent, requirements):
                continue

            # Load balancing score (prefer underutilized agents)
            load_factor = 1.0 - (agent.load_percentage / 100.0)
            load_deviation = abs(agent.load_percentage - avg_load_percentage) / 100.0
            load_balance_score = load_factor * (1.0 - load_deviation)

            # Standard scoring
            capability_score = self._calculate_capability_score(agent, requirements)
            tool_score = self._calculate_tool_score(agent, requirements)

            # Load-balanced weights
            total_score = (
                0.30 * capability_score +
                0.25 * tool_score +
                0.35 * load_balance_score +
                0.10 * self._calculate_availability_score(agent)
            )

            match = CapabilityMatchResult(
                agent_id=agent.agent_id,
                match_score=total_score,
                capability_score=capability_score,
                tool_score=tool_score,
                load_score=load_balance_score,
                availability_score=self._calculate_availability_score(agent),
                estimated_execution_time=self._estimate_execution_time(agent, context),
                estimated_cost=self._estimate_cost(agent, context),
                confidence_level=capability_score * tool_score
            )

            matches.append(match)

        return matches

    async def _cost_optimized_matching(
        self,
        agents: List[AgentPoolEntry],
        requirements: CapabilityFilter,
        context: MatchingContext
    ) -> List[CapabilityMatchResult]:
        """Cost-optimized matching to minimize execution costs."""

        matches = []

        for agent in agents:
            if not self._passes_basic_requirements(agent, requirements):
                continue

            # Cost efficiency calculations
            estimated_cost = self._estimate_cost(agent, context)
            cost_score = self._calculate_cost_efficiency_score(estimated_cost, context)

            # Basic capability requirements
            capability_score = self._calculate_capability_score(agent, requirements)
            tool_score = self._calculate_tool_score(agent, requirements)

            # Filter by budget if specified
            if context.budget_limit and estimated_cost > context.budget_limit:
                continue

            # Cost-optimized weights
            total_score = (
                0.25 * capability_score +
                0.20 * tool_score +
                0.40 * cost_score +
                0.15 * self._calculate_availability_score(agent)
            )

            match = CapabilityMatchResult(
                agent_id=agent.agent_id,
                match_score=total_score,
                capability_score=capability_score,
                tool_score=tool_score,
                estimated_cost=estimated_cost,
                estimated_execution_time=self._estimate_execution_time(agent, context),
                confidence_level=capability_score * tool_score
            )

            matches.append(match)

        return matches

    async def _multi_objective_matching(
        self,
        agents: List[AgentPoolEntry],
        requirements: CapabilityFilter,
        context: MatchingContext
    ) -> List[CapabilityMatchResult]:
        """Multi-objective optimization matching using Pareto efficiency."""

        # Define objectives based on context
        objectives = [
            OptimizationObjective.MAXIMIZE_RELIABILITY,
            OptimizationObjective.MINIMIZE_TIME,
            OptimizationObjective.MINIMIZE_COST,
            OptimizationObjective.BALANCE_LOAD
        ]

        matches = []
        objective_scores = {}

        for agent in agents:
            if not self._passes_basic_requirements(agent, requirements):
                continue

            # Calculate scores for each objective
            scores = {}
            scores[OptimizationObjective.MAXIMIZE_RELIABILITY] = self._calculate_reliability_score(agent)
            scores[OptimizationObjective.MINIMIZE_TIME] = 1.0 - self._normalize_execution_time(
                self._estimate_execution_time(agent, context)
            )
            scores[OptimizationObjective.MINIMIZE_COST] = self._calculate_cost_efficiency_score(
                self._estimate_cost(agent, context), context
            )
            scores[OptimizationObjective.BALANCE_LOAD] = 1.0 - (agent.load_percentage / 100.0)

            objective_scores[agent.agent_id] = scores

            # Calculate composite score using weighted sum
            weights = self._get_objective_weights(context)
            composite_score = sum(weights.get(obj, 0.25) * score for obj, score in scores.items())

            match = CapabilityMatchResult(
                agent_id=agent.agent_id,
                match_score=composite_score,
                capability_score=self._calculate_capability_score(agent, requirements),
                tool_score=self._calculate_tool_score(agent, requirements),
                performance_score=scores[OptimizationObjective.MAXIMIZE_RELIABILITY],
                estimated_execution_time=self._estimate_execution_time(agent, context),
                estimated_cost=self._estimate_cost(agent, context),
                confidence_level=min(scores.values())
            )

            matches.append(match)

        # Apply Pareto filtering to remove dominated solutions
        pareto_matches = self._pareto_filter(matches, objective_scores, objectives)

        return pareto_matches

    async def _ml_based_matching(
        self,
        agents: List[AgentPoolEntry],
        requirements: CapabilityFilter,
        context: MatchingContext
    ) -> List[CapabilityMatchResult]:
        """Machine learning-based matching using historical performance data."""

        matches = []

        for agent in agents:
            if not self._passes_basic_requirements(agent, requirements):
                continue

            # Use historical data to predict success probability
            prediction_score = self._predict_success_probability(agent, requirements, context)

            # Combine with traditional scoring
            capability_score = self._calculate_capability_score(agent, requirements)
            tool_score = self._calculate_tool_score(agent, requirements)

            # ML-enhanced weights
            total_score = (
                0.20 * capability_score +
                0.15 * tool_score +
                0.50 * prediction_score +
                0.15 * self._calculate_availability_score(agent)
            )

            match = CapabilityMatchResult(
                agent_id=agent.agent_id,
                match_score=total_score,
                capability_score=capability_score,
                tool_score=tool_score,
                performance_score=prediction_score,
                estimated_execution_time=self._estimate_execution_time(agent, context),
                estimated_cost=self._estimate_cost(agent, context),
                confidence_level=prediction_score
            )

            matches.append(match)

        return matches

    # Helper methods for scoring calculations

    def _calculate_capability_score(self, agent: AgentPoolEntry, requirements: CapabilityFilter) -> float:
        """Calculate capability matching score."""
        if not requirements.step_types:
            return 1.0

        matched_count = 0
        for step_type in requirements.step_types:
            for capability in agent.capabilities:
                if step_type in capability.supported_step_types:
                    matched_count += 1
                    break

        return matched_count / len(requirements.step_types)

    def _calculate_tool_score(self, agent: AgentPoolEntry, requirements: CapabilityFilter) -> float:
        """Calculate tool availability score."""
        if not requirements.required_tools:
            return 1.0

        available_tools = set(agent.available_tools)
        required_tools = set(requirements.required_tools)
        matched_tools = required_tools.intersection(available_tools)

        return len(matched_tools) / len(required_tools)

    def _calculate_workflow_score(self, agent: AgentPoolEntry, requirements: CapabilityFilter) -> float:
        """Calculate workflow support score."""
        if not requirements.workflow_types:
            return 1.0

        supported_count = sum(
            1 for workflow in requirements.workflow_types
            if agent.supports_workflow(workflow)
        )

        return supported_count / len(requirements.workflow_types)

    def _calculate_performance_score(self, agent: AgentPoolEntry, context: MatchingContext) -> float:
        """Calculate performance score based on historical metrics."""
        if not agent.performance_metrics:
            return 0.8  # Default assumption

        total_success_rate = 0.0
        total_speed_score = 0.0
        metric_count = 0

        for capability_name, metrics in agent.performance_metrics.items():
            total_success_rate += metrics.success_rate

            # Speed score based on average execution time
            if metrics.average_execution_time > 0:
                # Normalize against expected time
                speed_score = min(1.0, context.estimated_duration / metrics.average_execution_time)
                total_speed_score += speed_score
            else:
                total_speed_score += 0.8

            metric_count += 1

        if metric_count == 0:
            return 0.8

        avg_success_rate = total_success_rate / metric_count
        avg_speed_score = total_speed_score / metric_count

        return (avg_success_rate + avg_speed_score) / 2

    def _calculate_availability_score(self, agent: AgentPoolEntry) -> float:
        """Calculate availability score."""
        health_scores = {
            HealthStatus.HEALTHY: 1.0,
            HealthStatus.WARNING: 0.7,
            HealthStatus.CRITICAL: 0.3,
            HealthStatus.OFFLINE: 0.0,
            HealthStatus.UNKNOWN: 0.5
        }

        health_score = health_scores.get(agent.health_status, 0.5)
        load_score = max(0.0, 1.0 - (agent.load_percentage / 100.0))

        return (health_score + load_score) / 2

    def _calculate_cost_score(self, agent: AgentPoolEntry, context: MatchingContext) -> float:
        """Calculate cost efficiency score."""
        estimated_cost = self._estimate_cost(agent, context)
        return self._calculate_cost_efficiency_score(estimated_cost, context)

    def _calculate_reliability_score(self, agent: AgentPoolEntry) -> float:
        """Calculate reliability score based on error rates and uptime."""
        if not agent.performance_metrics:
            return 0.8

        total_reliability = 0.0
        metric_count = 0

        for metrics in agent.performance_metrics.values():
            reliability = 1.0 - metrics.error_rate
            total_reliability += reliability
            metric_count += 1

        if metric_count == 0:
            return 0.8

        avg_reliability = total_reliability / metric_count

        # Factor in uptime
        uptime_score = min(1.0, agent.uptime_hours / 24.0)  # Normalize to 24 hours

        return (avg_reliability + uptime_score) / 2

    def _calculate_speed_score(self, agent: AgentPoolEntry, context: MatchingContext) -> float:
        """Calculate speed score based on execution time."""
        estimated_time = self._estimate_execution_time(agent, context)

        if context.deadline:
            time_available = (context.deadline - datetime.utcnow()).total_seconds()
            if time_available > 0:
                return min(1.0, time_available / estimated_time)

        # Default speed scoring based on typical execution time
        reference_time = context.estimated_duration
        return min(1.0, reference_time / estimated_time) if estimated_time > 0 else 1.0

    def _calculate_cost_efficiency_score(self, cost: float, context: MatchingContext) -> float:
        """Calculate cost efficiency score."""
        if cost <= 0:
            return 1.0

        if context.budget_limit:
            if cost > context.budget_limit:
                return 0.0
            return 1.0 - (cost / context.budget_limit)

        # Default cost efficiency (assuming lower cost is better)
        max_reasonable_cost = 10.0  # Adjust based on typical costs
        return max(0.0, 1.0 - (cost / max_reasonable_cost))

    def _estimate_execution_time(self, agent: AgentPoolEntry, context: MatchingContext) -> float:
        """Estimate execution time for the agent."""
        if agent.performance_metrics:
            avg_times = [
                metrics.average_execution_time
                for metrics in agent.performance_metrics.values()
                if metrics.average_execution_time > 0
            ]
            if avg_times:
                base_time = statistics.mean(avg_times)
            else:
                base_time = context.estimated_duration
        else:
            base_time = context.estimated_duration

        # Adjust for current load
        load_factor = 1.0 + (agent.load_percentage / 100.0) * 0.5

        return base_time * load_factor

    def _estimate_cost(self, agent: AgentPoolEntry, context: MatchingContext) -> float:
        """Estimate execution cost for the agent."""
        base_cost = agent.cost_per_execution

        if base_cost <= 0:
            # Estimate based on agent type and complexity
            base_cost = 0.1  # Default base cost

            # Adjust for complexity
            if agent.agent_type in ['super', 'expert']:
                base_cost *= 2.0
            elif agent.agent_type in ['specialist', 'advanced']:
                base_cost *= 1.5

        # Factor in execution time
        execution_time = self._estimate_execution_time(agent, context)
        time_factor = execution_time / 300.0  # Normalize to 5 minutes

        return base_cost * time_factor

    def _calculate_fuzzy_similarity(self, str1: str, str2: str) -> float:
        """Calculate fuzzy similarity between two strings."""
        if str1 == str2:
            return 1.0

        # Simple fuzzy matching based on common substrings
        str1_lower = str1.lower()
        str2_lower = str2.lower()

        # Exact match
        if str1_lower == str2_lower:
            return 1.0

        # Substring matching
        if str1_lower in str2_lower or str2_lower in str1_lower:
            return 0.8

        # Common words
        words1 = set(str1_lower.split('_'))
        words2 = set(str2_lower.split('_'))
        common_words = words1.intersection(words2)

        if common_words:
            return len(common_words) / max(len(words1), len(words2))

        return 0.0

    def _passes_basic_requirements(self, agent: AgentPoolEntry, requirements: CapabilityFilter) -> bool:
        """Check if agent passes basic requirements."""
        # Health check
        if requirements.health_statuses and agent.health_status not in requirements.health_statuses:
            return False

        # Load check
        if agent.load_percentage > requirements.max_current_load:
            return False

        # Capacity check
        available_capacity = agent.max_concurrent_executions - agent.current_load
        if available_capacity < requirements.min_available_capacity:
            return False

        return True

    def _get_contextual_weights(self, context: MatchingContext) -> MatchingWeights:
        """Get weights based on context preferences."""
        weights = MatchingWeights()

        # Adjust weights based on context
        if context.prefer_reliable:
            weights.performance_history += 0.1
            weights.capability_match -= 0.05
            weights.availability += 0.05

        if context.priority >= 8:  # High priority
            weights.availability += 0.1
            weights.performance_history += 0.1
            weights.cost_efficiency -= 0.2

        if context.budget_limit:
            weights.cost_efficiency += 0.15
            weights.capability_match -= 0.075
            weights.performance_history -= 0.075

        return weights.normalize()

    def _get_objective_weights(self, context: MatchingContext) -> Dict[OptimizationObjective, float]:
        """Get objective weights for multi-objective optimization."""
        weights = {
            OptimizationObjective.MAXIMIZE_RELIABILITY: 0.3,
            OptimizationObjective.MINIMIZE_TIME: 0.25,
            OptimizationObjective.MINIMIZE_COST: 0.2,
            OptimizationObjective.BALANCE_LOAD: 0.25
        }

        # Adjust based on context
        if context.prefer_reliable:
            weights[OptimizationObjective.MAXIMIZE_RELIABILITY] += 0.2
            weights[OptimizationObjective.MINIMIZE_TIME] -= 0.1
            weights[OptimizationObjective.MINIMIZE_COST] -= 0.1

        if context.deadline:
            weights[OptimizationObjective.MINIMIZE_TIME] += 0.2
            weights[OptimizationObjective.BALANCE_LOAD] -= 0.1
            weights[OptimizationObjective.MINIMIZE_COST] -= 0.1

        if context.budget_limit:
            weights[OptimizationObjective.MINIMIZE_COST] += 0.2
            weights[OptimizationObjective.MAXIMIZE_RELIABILITY] -= 0.1
            weights[OptimizationObjective.BALANCE_LOAD] -= 0.1

        return weights

    def _normalize_execution_time(self, execution_time: float) -> float:
        """Normalize execution time to 0-1 scale."""
        max_reasonable_time = 3600.0  # 1 hour
        return min(1.0, execution_time / max_reasonable_time)

    def _pareto_filter(
        self,
        matches: List[CapabilityMatchResult],
        objective_scores: Dict[str, Dict[OptimizationObjective, float]],
        objectives: List[OptimizationObjective]
    ) -> List[CapabilityMatchResult]:
        """Filter matches using Pareto efficiency."""
        pareto_matches = []

        for i, match_a in enumerate(matches):
            is_dominated = False

            for j, match_b in enumerate(matches):
                if i == j:
                    continue

                scores_a = objective_scores[match_a.agent_id]
                scores_b = objective_scores[match_b.agent_id]

                # Check if match_a is dominated by match_b
                all_worse_or_equal = True
                at_least_one_worse = False

                for obj in objectives:
                    score_a = scores_a[obj]
                    score_b = scores_b[obj]

                    if score_a > score_b:
                        all_worse_or_equal = False
                        break
                    elif score_a < score_b:
                        at_least_one_worse = True

                if all_worse_or_equal and at_least_one_worse:
                    is_dominated = True
                    break

            if not is_dominated:
                pareto_matches.append(match_a)

        return pareto_matches

    def _predict_success_probability(
        self,
        agent: AgentPoolEntry,
        requirements: CapabilityFilter,
        context: MatchingContext
    ) -> float:
        """Predict success probability using historical data."""
        # Simple ML prediction based on historical patterns
        base_probability = 0.8

        # Adjust based on performance metrics
        if agent.performance_metrics:
            success_rates = [
                metrics.success_rate
                for metrics in agent.performance_metrics.values()
            ]
            if success_rates:
                avg_success_rate = statistics.mean(success_rates)
                base_probability = avg_success_rate

        # Adjust based on capability match
        capability_score = self._calculate_capability_score(agent, requirements)
        tool_score = self._calculate_tool_score(agent, requirements)

        # Simple prediction model
        prediction = (
            0.4 * base_probability +
            0.3 * capability_score +
            0.2 * tool_score +
            0.1 * self._calculate_availability_score(agent)
        )

        return min(prediction, 1.0)

    def _calculate_confidence(self, agent: AgentPoolEntry, requirements: CapabilityFilter) -> float:
        """Calculate confidence in the match."""
        capability_score = self._calculate_capability_score(agent, requirements)
        tool_score = self._calculate_tool_score(agent, requirements)
        availability_score = self._calculate_availability_score(agent)

        # Confidence is the product of key factors
        return capability_score * tool_score * availability_score

    async def _record_matching_result(
        self,
        requirements: CapabilityFilter,
        context: MatchingContext,
        results: List[CapabilityMatchResult],
        algorithm: MatchingAlgorithm
    ):
        """Record matching result for learning purposes."""
        try:
            record = {
                "timestamp": datetime.utcnow().isoformat(),
                "algorithm": algorithm.value,
                "requirements": {
                    "step_types": requirements.step_types,
                    "required_tools": requirements.required_tools,
                    "workflow_types": requirements.workflow_types
                },
                "context": {
                    "priority": context.priority,
                    "estimated_duration": context.estimated_duration,
                    "environment": context.environment
                },
                "results_count": len(results),
                "top_match_score": results[0].match_score if results else 0.0
            }

            self.matching_history.append(record)

            # Keep only recent history (last 1000 records)
            if len(self.matching_history) > 1000:
                self.matching_history = self.matching_history[-1000:]

        except Exception as e:
            logger.warning(f"Failed to record matching result: {e}")


# Global matcher instance
_capability_matcher: Optional[AdvancedCapabilityMatcher] = None


def get_capability_matcher() -> AdvancedCapabilityMatcher:
    """Get or create the global capability matcher instance."""
    global _capability_matcher

    if _capability_matcher is None:
        _capability_matcher = AdvancedCapabilityMatcher()

    return _capability_matcher


async def find_best_agent_matches(
    agents: List[AgentPoolEntry],
    requirements: CapabilityFilter,
    context: MatchingContext = None,
    algorithm: MatchingAlgorithm = MatchingAlgorithm.WEIGHTED_SCORE,
    max_results: int = 10
) -> List[CapabilityMatchResult]:
    """
    Convenience function to find best agent matches.

    Args:
        agents: Available agents
        requirements: Capability requirements
        context: Matching context
        algorithm: Matching algorithm to use
        max_results: Maximum results to return

    Returns:
        List of capability match results
    """
    if context is None:
        context = MatchingContext()

    matcher = get_capability_matcher()
    return await matcher.find_best_matches(
        agents, requirements, context, algorithm, max_results
    )
