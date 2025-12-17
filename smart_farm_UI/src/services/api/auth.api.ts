import type { LoginReq, LoginRes } from "@/types/Auth.type";
import axiosInstance from "../axios";
import type { ApiResponse } from "@/types/api.types";

export const loginApi = (data: LoginReq):
    Promise<ApiResponse<LoginRes>> => {
  return axiosInstance.post("/auth/login", data);
};
