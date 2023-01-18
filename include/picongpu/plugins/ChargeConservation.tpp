/* Copyright 2013-2022 Axel Huebl, Heiko Burau, Rene Widera, Felix Schmitt
 *
 * This file is part of PIConGPU.
 *
 * PIConGPU is free software: you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 *
 * PIConGPU is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with PIConGPU.
 * If not, see <http://www.gnu.org/licenses/>.
 */

#pragma once

#include "common/txtFileHandling.hpp"
#include "picongpu/fields/FieldJ.hpp"

#include <pmacc/dataManagement/DataConnector.hpp>
#include <pmacc/mappings/kernel/AreaMapping.hpp>
#include <pmacc/math/Vector.hpp>
#include <pmacc/math/operation.hpp>
#include <pmacc/math/vector/Float.hpp>
#include <pmacc/math/vector/Int.hpp>
#include <pmacc/math/vector/Size_t.hpp>
#include <pmacc/meta/ForEach.hpp>
#include <pmacc/particles/meta/FindByNameOrType.hpp>
#include <pmacc/static_assert.hpp>

#include <sstream>


namespace picongpu
{
    ChargeConservation::ChargeConservation()
        : name("ChargeConservation: Print the maximum charge deviation between particles and div E to textfile "
               "'chargeConservation.dat'")
        , prefix("chargeConservation")
        , filename("chargeConservation.dat")
        , cellDescription(nullptr)
    {
        Environment<>::get().PluginConnector().registerPlugin(this);
    }

    void ChargeConservation::pluginRegisterHelp(po::options_description& desc)
    {
        desc.add_options()(
            (this->prefix + ".period").c_str(),
            po::value<std::string>(&this->notifyPeriod),
            "enable plugin [for each n-th step]");
    }

    std::string ChargeConservation::pluginGetName() const
    {
        return this->name;
    }

    void ChargeConservation::pluginLoad()
    {
        if(this->notifyPeriod.empty())
            return;

        Environment<>::get().PluginConnector().setNotificationPeriod(this, this->notifyPeriod);

        constexpr uint32_t reductionMainMemSize = 1024u;
        globalReduce = std::make_unique<algorithms::GlobalReduce>(reductionMainMemSize);
        // all MPI ranks will participate
        globalReduce->participate(true);

        if(globalReduce->hasResult(mpiReduceMethod))
        {
            this->output_file.open(this->filename.c_str(), std::ios_base::app);
            this->output_file << "#timestep max-charge-deviation unit[As]" << std::endl;
        }
    }

    void ChargeConservation::restart(uint32_t restartStep, const std::string restartDirectory)
    {
        if(this->notifyPeriod.empty())
            return;

        if(!globalReduce->hasResult(mpiReduceMethod))
            return;

        restoreTxtFile(this->output_file, this->filename, restartStep, restartDirectory);
    }

    void ChargeConservation::checkpoint(uint32_t currentStep, const std::string checkpointDirectory)
    {
        if(this->notifyPeriod.empty())
            return;

        if(!globalReduce->hasResult(mpiReduceMethod))
            return;

        checkpointTxtFile(this->output_file, this->filename, currentStep, checkpointDirectory);
    }

    void ChargeConservation::setMappingDescription(MappingDesc* cellDescription)
    {
        this->cellDescription = cellDescription;
    }

    namespace detail
    {
        /**
         * @class Div
         * @brief divergence functor for 2D and 3D
         *
         * NOTE: This functor uses a Yee-cell stencil.
         */
        template<int dim, typename ValueType>
        struct Div;

        template<typename ValueType>
        struct Div<DIM3, ValueType>
        {
            using result_type = ValueType;

            template<typename Field>
            HDINLINE ValueType operator()(Field field) const
            {
                const ValueType reciWidth = float_X(1.0) / cellSize.x();
                const ValueType reciHeight = float_X(1.0) / cellSize.y();
                const ValueType reciDepth = float_X(1.0) / cellSize.z();
                return ((*field).x() - field(DataSpace<DIM3>(-1, 0, 0)).x()) * reciWidth
                    + ((*field).y() - field(DataSpace<DIM3>(0, -1, 0)).y()) * reciHeight
                    + ((*field).z() - field(DataSpace<DIM3>(0, 0, -1)).z()) * reciDepth;
            }
        };

        template<typename ValueType>
        struct Div<DIM2, ValueType>
        {
            using result_type = ValueType;

            template<typename Field>
            HDINLINE ValueType operator()(Field field) const
            {
                const ValueType reciWidth = float_X(1.0) / cellSize.x();
                const ValueType reciHeight = float_X(1.0) / cellSize.y();
                return ((*field).x() - (field(DataSpace<DIM2>(-1, 0))).x()) * reciWidth
                    + ((*field).y() - (field(DataSpace<DIM2>(0, -1))).y()) * reciHeight;
            }
        };

        // functor for all species to calculate density
        template<typename T_SpeciesType, typename T_Area>
        struct ComputeChargeDensity
        {
            using SpeciesType = pmacc::particles::meta::FindByNameOrType_t<VectorAllSpecies, T_SpeciesType>;
            static const uint32_t area = T_Area::value;

            HINLINE void operator()(FieldTmp* fieldTmp, const uint32_t currentStep) const
            {
                DataConnector& dc = Environment<>::get().DataConnector();

                /* load species without copying the particle data to the host */
                auto speciesTmp = dc.get<SpeciesType>(SpeciesType::FrameType::getName(), true);

                /* run algorithm */
                using ChargeDensitySolver = typename particles::particleToGrid::CreateFieldTmpOperation_t<
                    SpeciesType,
                    particles::particleToGrid::derivedAttributes::ChargeDensity>::Solver;

                fieldTmp->computeValue<area, ChargeDensitySolver>(*speciesTmp, currentStep);
            }
        };
    } // namespace detail

    void ChargeConservation::notify(uint32_t currentStep)
    {
        typedef SuperCellSize BlockDim;

        DataConnector& dc = Environment<>::get().DataConnector();

        /* load FieldTmp without copy data to host */
        PMACC_CASSERT_MSG(_please_allocate_at_least_one_FieldTmp_in_memory_param, fieldTmpNumSlots > 0);
        auto fieldTmp = dc.get<FieldTmp>(FieldTmp::getUniqueId(0), true);
        /* reset density values to zero */
        fieldTmp->getGridBuffer().getDeviceBuffer().setValue(FieldTmp::ValueType(0.0));

        using EligibleSpecies = typename bmpl::
            copy_if<VectorAllSpecies, particles::traits::SpeciesEligibleForSolver<bmpl::_1, ChargeConservation>>::type;

        // todo: log species that are used / ignored in this plugin with INFO

        /* calculate and add the charge density values from all species in FieldTmp */
        meta::ForEach<
            EligibleSpecies,
            picongpu::detail::ComputeChargeDensity<bmpl::_1, bmpl::int_<CORE + BORDER>>,
            bmpl::_1>
            computeChargeDensity;
        computeChargeDensity(fieldTmp.get(), currentStep);

        /* add results of all species that are still in GUARD to next GPUs BORDER */
        EventTask fieldTmpEvent = fieldTmp->asyncCommunication(__getTransactionEvent());
        __setTransactionEvent(fieldTmpEvent);

        auto fieldE = dc.get<FieldE>(FieldE::getName(), true);

        auto const chargeDeviation = [] ALPAKA_FN_ACC(auto const& worker, auto mapper, auto rohBox, auto fieldEBox)
        {
            DataSpace<simDim> const superCellIdx(
                mapper.getSuperCellIndex(DataSpace<simDim>(cupla::blockIdx(worker.getAcc()))));
            DataSpace<simDim> const supercellCellIdx = superCellIdx * SuperCellSize::toRT();
            constexpr uint32_t cellsPerSupercell = pmacc::math::CT::volume<SuperCellSize>::type::value;

            lockstep::makeForEach<cellsPerSupercell>(worker)(
                [&](uint32_t const linearIdx)
                {
                    // cell index within the superCell
                    DataSpace<simDim> const inSupercellCellIdx
                        = DataSpaceOperations<simDim>::template map<SuperCellSize>(linearIdx);
                    auto globalCellIdx = supercellCellIdx + inSupercellCellIdx;

                    auto div = picongpu::detail::Div<simDim, typename FieldTmp::ValueType>{};

                    /* rho := | div E * eps_0 - rho | */
                    rohBox(globalCellIdx).x()
                        = math::abs(div(fieldEBox.shift(globalCellIdx)) * EPS0 - rohBox(globalCellIdx).x());
                });
        };

        auto const mapper = makeAreaMapper<CORE + BORDER>(*this->cellDescription);
        auto const workerCfg = lockstep::makeWorkerCfg(SuperCellSize{});
        PMACC_LOCKSTEP_KERNEL(chargeDeviation, workerCfg)
        (mapper.getGridDim())(
            mapper,
            fieldTmp->getGridBuffer().getDeviceBuffer().getDataBox(),
            fieldE->getGridBuffer().getDeviceBuffer().getDataBox());

        // find global max error
        auto memLayoutRoh = fieldTmp->getGridLayout();
        int localSizeRoh = memLayoutRoh.getDataSpaceWithoutGuarding().productOfComponents();

        using D1Box = DataBoxDim1Access<typename FieldTmp::DataBoxType>;
        // ignore guards and operate on CORE+BORDER only
        D1Box d1access(
            fieldTmp->getGridBuffer().getDeviceBuffer().getDataBox().shift(memLayoutRoh.getGuard()),
            memLayoutRoh.getDataSpaceWithoutGuarding());

        auto maxChargeDiff = (*globalReduce)(pmacc::math::operation::Max(), d1access, localSizeRoh, mpiReduceMethod);

        if(globalReduce->hasResult(mpiReduceMethod))
        {
            this->output_file << currentStep << " " << (maxChargeDiff * CELL_VOLUME).x() << " " << UNIT_CHARGE
                              << std::endl;
        }
    }

} // namespace picongpu
