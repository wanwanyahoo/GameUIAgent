using System;
using System.IO;
using System.Net;
using System.Text;
using UnityEngine;

namespace GameUIAgent.Editor
{
    public sealed class GameUIAgentBackendBridge
    {
        public GameUIAgentBuildIrResult BuildIr(GameUIAgentBuildIrRequest request)
        {
            if (request == null)
            {
                throw new ArgumentException("build_ir request is required");
            }

            if (string.IsNullOrWhiteSpace(request.api_base_url))
            {
                throw new ArgumentException("build_ir requires api_base_url");
            }

            if (string.IsNullOrWhiteSpace(request.access_token))
            {
                throw new ArgumentException("build_ir requires access_token");
            }

            if (string.IsNullOrWhiteSpace(request.project_id))
            {
                throw new ArgumentException("build_ir requires project_id");
            }

            if (string.IsNullOrWhiteSpace(request.engine))
            {
                throw new ArgumentException("build_ir requires engine");
            }

            string snapshotId = request.snapshot_id;
            if (string.IsNullOrWhiteSpace(snapshotId))
            {
                if (string.IsNullOrWhiteSpace(request.snapshot_json))
                {
                    throw new ArgumentException("build_ir requires snapshot_json or snapshot_id");
                }

                snapshotId = CreateSnapshot(request);
            }

            string buildIrResponseJson = SendJsonRequest(
                "POST",
                request.api_base_url.TrimEnd('/') + "/api/plugin/engine-snapshots/" + snapshotId + "/build-ir",
                request.access_token,
                string.Empty);

            BuildIrResponse payload = JsonUtility.FromJson<BuildIrResponse>(buildIrResponseJson);
            if (payload == null || payload.ir == null || string.IsNullOrWhiteSpace(payload.ir.id))
            {
                throw new InvalidOperationException("build_ir backend returned an invalid response");
            }

            return new GameUIAgentBuildIrResult
            {
                project_id = request.project_id,
                snapshot_id = payload.snapshot_id,
                ir_id = payload.ir.id,
                version_id = payload.ir.version_id,
                status = "ok",
                payload_json = buildIrResponseJson
            };
        }

        private string CreateSnapshot(GameUIAgentBuildIrRequest request)
        {
            string snapshotResponseJson = SendJsonRequest(
                "POST",
                request.api_base_url.TrimEnd('/') + "/api/projects/" + request.project_id + "/engine-snapshots",
                request.access_token,
                request.snapshot_json);

            CreateSnapshotResponse payload = JsonUtility.FromJson<CreateSnapshotResponse>(snapshotResponseJson);
            if (payload == null || string.IsNullOrWhiteSpace(payload.id))
            {
                throw new InvalidOperationException("engine snapshot backend returned an invalid response");
            }
            return payload.id;
        }

        private static string SendJsonRequest(string method, string url, string accessToken, string body)
        {
            HttpWebRequest httpRequest = WebRequest.CreateHttp(url);
            httpRequest.Method = method;
            httpRequest.ContentType = "application/json";
            httpRequest.Accept = "application/json";
            httpRequest.Headers[HttpRequestHeader.Authorization] = "Bearer " + accessToken;

            if (!string.IsNullOrWhiteSpace(body))
            {
                byte[] bodyBytes = Encoding.UTF8.GetBytes(body);
                using (Stream requestStream = httpRequest.GetRequestStream())
                {
                    requestStream.Write(bodyBytes, 0, bodyBytes.Length);
                }
            }

            try
            {
                using (HttpWebResponse response = (HttpWebResponse)httpRequest.GetResponse())
                using (StreamReader reader = new StreamReader(response.GetResponseStream()))
                {
                    return reader.ReadToEnd();
                }
            }
            catch (WebException ex)
            {
                string details = ex.Message;
                if (ex.Response != null)
                {
                    using (StreamReader reader = new StreamReader(ex.Response.GetResponseStream()))
                    {
                        details = reader.ReadToEnd();
                    }
                }
                throw new InvalidOperationException("Backend bridge failed: " + details, ex);
            }
        }

        [Serializable]
        private sealed class CreateSnapshotResponse
        {
            public string id;
        }

        [Serializable]
        private sealed class BuildIrResponse
        {
            public string snapshot_id;
            public IrPayload ir;
        }

        [Serializable]
        private sealed class IrPayload
        {
            public string id;
            public string version_id;
        }
    }
}
