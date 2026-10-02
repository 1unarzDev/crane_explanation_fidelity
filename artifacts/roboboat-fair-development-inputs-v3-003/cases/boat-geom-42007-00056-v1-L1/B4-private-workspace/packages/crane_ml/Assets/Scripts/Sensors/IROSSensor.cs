using System;
using Sim.Utils.ROS;

namespace Sim.Sensors {
    public interface IROSSensor<T> where T : Unity.Robotics.ROSTCPConnector.MessageGeneration.Message {
        ROSPublisher publisher { get; set; }
        T CreateMessage();
    }
}
